import json
import time
import ctypes

from pydantic import BaseModel, Field
from pynput import keyboard
from pynput.mouse import Controller as MouseController
from pynput.keyboard import Key, Listener, KeyCode
import pyautogui
import pydirectinput

# Make pydirectinput as fast and game-friendly as possible
pydirectinput.PAUSE = 0
pydirectinput.FAILSAFE = False

from event import (RecordingEvent, MouseMoveEvent, MouseClickEvent,
                   MouseScrollEvent, KeyPressEvent, KeyReleaseEvent, MousePositionEvent, WaitEvent, ImageClickEvent,
                   RunRecordingEvent)

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # 2 = PROCESS_PER_MONITOR_DPI_AWARE
    print("DPI awareness enabled → mouse coordinates should now match")
except Exception as e:
    print(f"Could not set DPI awareness: {e} (try running as admin or ignore on non-Windows)")

class EventPlayer(BaseModel):
    playing: bool = Field(default=False)
    start_playing_key: Key = Key.f7
    stop_playing_key: Key = Key.f8
    input_file_path: str = Field(default="recording.json")
    __events: list[RecordingEvent] = []
    __start_time: float = None
    __mouse: MouseController = None  # still used for scroll events
    __keyboard_listener: Listener = None
    currently_pressed_keys: set = set()
    pressed_mouse_buttons: set = set()
    speed_multiplier: float = 1.0  # 0.5 = half speed, 2.0 = double speed

    @staticmethod
    def _recording_event_factory(data: dict) -> RecordingEvent:
        event_type = data.get("type")
        event_map = {
            "MouseMoveEvent": MouseMoveEvent,
            "MouseClickEvent": MouseClickEvent,
            "MouseScrollEvent": MouseScrollEvent,
            "MousePositionEvent": MousePositionEvent,
            "KeyPressEvent": KeyPressEvent,
            "KeyReleaseEvent": KeyReleaseEvent,
            "WaitEvent": WaitEvent,
            "ImageClickEvent": ImageClickEvent,
            "RunRecordingEvent": RunRecordingEvent,
        }

        cls = event_map.get(event_type)
        if not cls:
            raise ValueError(f"Unknown event type: {event_type}")
        return cls.model_validate(data)

    def load_recording_file(self) -> None:
        with open(self.input_file_path, "r") as f:
            raw_data = json.load(f)
            self.__events = [self._recording_event_factory(item) for item in raw_data]

    def start_playing(self) -> None:
        if self.playing:
            raise RuntimeError("Already playing")
        self.__mouse = MouseController()
        self.__start_time = time.perf_counter()

        self.playing = True
        print(f"Playback started (speed: ×{self.speed_multiplier})")

    def stop_playing(self) -> None:
        if not self.playing:
            raise RuntimeError("Not currently playing")
        self.playing = False

        # Release any keys we think are still held down via DirectInput
        for key_str in list(self.currently_pressed_keys):
            try:
                pydirectinput.keyUp(self.__str_to_pydirect_key(key_str))
            except Exception as e:
                print(f"Warning: could not release key {key_str!r}: {e}")
        self.currently_pressed_keys.clear()

        # Release any pressed mouse buttons via DirectInput
        for button in list(self.pressed_mouse_buttons):
            try:
                pydirectinput.mouseUp(button=button)
            except Exception as e:
                print(f"Warning: could not release mouse button {button!r}: {e}")
        self.pressed_mouse_buttons.clear()

        print(f"Stopped playing recording {self.input_file_path}")

    def __apply_mouse_delta(self, dx: int, dy: int) -> None:
        if dx == 0 and dy == 0:
            return
        pydirectinput.moveRel(dx, dy)

    @staticmethod
    def __str_to_pydirect_key(s: str) -> str:
        if s.startswith("Key."):
            return s[4:]
        return s.replace("'", "")

    @staticmethod
    def __str_to_mouse_button(s: str) -> str:   
        if s is None:
            return "left"
        btn = str(s).lower().strip()
        # Strip common prefixes and quotes
        if btn.startswith("button."):
            btn = btn[len("button."):]
        btn = btn.replace("'", "").replace('"', "")
        if btn in ("left", "right", "middle"):
            return btn 
        return "left"

    def play_event(self, event: RecordingEvent) -> None:
        if isinstance(event, WaitEvent):
            time.sleep(event.duration_seconds / self.speed_multiplier)

        elif isinstance(event, MousePositionEvent):
            # Absolute move using DirectInput
            pydirectinput.moveTo(event.x, event.y)

        elif isinstance(event, MouseMoveEvent):
            self.__apply_mouse_delta(event.delta_x, event.delta_y)

        elif isinstance(event, MouseClickEvent): 
            button = self.__str_to_mouse_button(event.button)
            if event.pressed:
                pydirectinput.mouseDown(button=button)
                self.pressed_mouse_buttons.add(button)
            else:
                pydirectinput.mouseUp(button=button)
                self.pressed_mouse_buttons.discard(button)

        elif isinstance(event, MouseScrollEvent):
            # PyDirectInput does not support scroll → keep using pynput's mouse controller
            self.__mouse.scroll(event.scroll_dx, event.scroll_dy)

        elif isinstance(event, KeyPressEvent):
            key_name = self.__str_to_pydirect_key(event.key)
            pydirectinput.keyDown(key_name)
            self.currently_pressed_keys.add(event.key)

        elif isinstance(event, KeyReleaseEvent):
            key_name = self.__str_to_pydirect_key(event.key)
            pydirectinput.keyUp(key_name)
            self.currently_pressed_keys.discard(event.key)

        elif isinstance(event, ImageClickEvent):
            self._perform_image_click(event)

        elif isinstance(event, RunRecordingEvent):
            own_speed = event.speed_multiplier if event.speed_multiplier is not None else 1.0
            sub_player = EventPlayer(speed_multiplier=own_speed * self.speed_multiplier)
            sub_player.input_file_path = event.file_path
            sub_player.load_recording_file()

            sub_player.start_playing()
            sub_player._play_recording()
            print(f"Finished sub-recording: {event.file_path}")

    def __on_press(self, key: Key) -> None:
        if key == self.start_playing_key and not self.playing:
            self.start_playing()
        elif key == self.stop_playing_key and self.playing:
            self.stop_playing()

    def _listen(self) -> None:
        print(f"Press {self.start_playing_key} to start playing recording")
        print(f"Press {self.stop_playing_key} to stop")

        self.__keyboard_listener = keyboard.Listener(on_press=self.__on_press)
        self.__keyboard_listener.start()

    def _play_recording(self) -> None:
        if not self.playing:
            raise RuntimeError("Not currently playing")

        for event in self.__events:
            if not self.playing: break

            now = time.perf_counter() - self.__start_time
            target_time = event.time / self.speed_multiplier
            delay = target_time - now

            if delay > 0.001:
                time.sleep(delay)
            elif delay < -0.05:
                print(f"Warning: playback lagging behind by {-delay:.3f}s")

            self.play_event(event)
        if self.playing:
            self.stop_playing()

    def _perform_image_click(self, event: ImageClickEvent) -> None:
        start_time = time.perf_counter()
        found_pos = None

        while time.perf_counter() - start_time < (event.timeout_seconds or 30.0):
            try:
                found_pos = pyautogui.locateCenterOnScreen(
                    event.image_path,
                    confidence=event.confidence,
                    grayscale=event.grayscale,
                )
                if found_pos is not None:
                    break
            except pyautogui.ImageNotFoundException:
                pass

            time.sleep(0.4)

        if found_pos is None:
            msg = f"Image not found: {event.image_path} after {event.timeout_seconds or 30.0}s"
            if event.fail_action == "stop":
                print(msg + " → stopping playback")
                self.stop_playing()
                return
            else:
                print(msg + " → skipping to next event")
                return
 
        pydirectinput.moveTo(found_pos[0], found_pos[1]) 
        click_button = self.__str_to_mouse_button(event.button)
        pydirectinput.click(button=click_button)
        print(f"Clicked {event.button} on image {event.image_path} at {found_pos}")

    def run(self) -> None:
        self._listen()

        while True:
            if self.playing:
                self._play_recording()

if __name__ == "__main__":
    event_player = EventPlayer()
    event_player.load_recording_file()
    event_player.run()
