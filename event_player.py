import json
import time

from pydantic import BaseModel, Field
from pynput import keyboard
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key, Listener, KeyCode

from event import RecordingEvent, MouseMoveEvent, MouseClickEvent, MouseScrollEvent, KeyPressEvent, KeyReleaseEvent
# from overlay import Overlay


class EventPlayer(BaseModel):
    playing: bool = Field(default=False)
    start_playing_key: Key = Key.f7
    stop_playing_key: Key = Key.f8
    input_file_path: str = Field(default="recording.json")
    __events: list[RecordingEvent] = []
    __start_time: float = None
    __last_mouse_position: tuple[int, int] = None
    __mouse: MouseController = None
    __keyboard: KeyboardController = None
    __keyboard_listener: Listener = None
    currently_pressed_keys: set = set()
    pressed_mouse_buttons: set = set()
    # overlay: Overlay = None # TODO: interface show hide update

    @staticmethod
    def __recording_event_factory(data: dict) -> RecordingEvent:
        event_type = data.get("type")
        event_map = {
            "MouseMoveEvent": MouseMoveEvent,
            "MouseClickEvent": MouseClickEvent,
            "MouseScrollEvent": MouseScrollEvent,
            "KeyPressEvent": KeyPressEvent,
            "KeyReleaseEvent": KeyReleaseEvent,
        }

        cls = event_map.get(event_type)
        if not cls:
            raise ValueError(f"Unknown event type: {event_type}")
        return cls.model_validate(data)

    def load_recording_file(self) -> None:
        with open(self.input_file_path, "r") as f:
            raw_data = json.load(f)
            self.__events = [self.__recording_event_factory(item) for item in raw_data]

    def start_playing(self) -> None:
        if self.playing:
            raise RuntimeError("Already playing")
        self.__last_mouse_position = None
        self.__mouse = MouseController()
        self.__keyboard = KeyboardController()
        self.__start_time = time.time()

        self.playing = True
        #if self.overlay:
        #    self.overlay.show()

        print("Starting to play recording [Make sure your fullscreen]")

    def stop_playing(self) -> None:
        if not self.playing:
            raise RuntimeError("Not currently playing")
        self.playing = False

        #if self.overlay:
        #    self.overlay.hide()

        [self.__keyboard.release(self.__str_to_key(key)) for key in self.currently_pressed_keys]
        self.currently_pressed_keys.clear()
        self.__mouse.release(Button.left)
        self.__mouse.release(Button.right)

        print(f"Stopped playing recording {self.input_file_path}")

    def __apply_mouse_delta(self, dx: int, dy: int) -> None:

        self.__mouse.move(dx, dy)

    @staticmethod
    def __str_to_key(s: str) -> Key | KeyCode:
        if s.startswith("Key."):
            return getattr(Key, s[4:])
        return KeyCode.from_char(s.replace("'", ""))

    def play_event(self, event: RecordingEvent) -> None:
        if isinstance(event, MouseMoveEvent):
            self.__apply_mouse_delta(event.delta_x, event.delta_y)

        elif isinstance(event, MouseClickEvent):
            button = Button.left if "left" in event.button else Button.right
            if event.pressed:
                self.__mouse.press(button)
                self.pressed_mouse_buttons.add(button)
            else:
                self.__mouse.release(button)
                self.pressed_mouse_buttons.discard(button)

        elif isinstance(event, MouseScrollEvent):
            self.__mouse.scroll(event.scroll_dx, event.scroll_dy)

        elif isinstance(event, KeyPressEvent):
            key = self.__str_to_key(event.key)
            self.__keyboard.press(key)
            self.currently_pressed_keys.add(event.key)

        elif isinstance(event, KeyReleaseEvent):
            key = self.__str_to_key(event.key)
            self.__keyboard.release(key)
            self.currently_pressed_keys.discard(event.key)
        # self._update_overlay()

    """def _update_overlay(self):
        if self.overlay:
            self.overlay.update_overlay(
                mouse_pos=self.__mouse.position,
                keys=self.currently_pressed_keys,
                buttons={btn.name for btn in self.pressed_mouse_buttons}  # Update with pressed mouse buttons
            )"""

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
            if not self.playing:
                break

            now = time.time() - self.__start_time
            delay = event.time - now
            if delay > 0:
                time.sleep(delay)
            self.play_event(event)
        if self.playing:
            self.stop_playing()

    def run(self) -> None:
        self._listen()

        while True:
            if self.playing:
                self._play_recording()

if __name__ == "__main__":
    #overlay = Overlay()
    event_player = EventPlayer() #(overlay=overlay)
    event_player.load_recording_file()
    event_player.run()
