import json
import time

from pydantic import BaseModel, Field
from pynput.keyboard import Key
from pynput import mouse, keyboard
from pynput.mouse import Button

from event import RecordingEvent, MouseClickEvent, MouseMoveEvent, MouseScrollEvent, KeyPressEvent, KeyReleaseEvent


class EventRecorder(BaseModel):
    recording: bool = Field(default=False)
    start_recording_key: Key = Key.f7
    stop_recording_key: Key = Key.f7
    output_file_path: str = Field(default="recording.json")
    __events: list[RecordingEvent] = []
    __start_time: float = None
    __last_mouse_position: tuple[int, int] = None
    __mouse_listener: mouse.Listener = None
    __keyboard_listener: keyboard.Listener = None

    def start_recording(self) -> None:
        if self.recording:
            raise Exception # TODO: find a proper exception or make one
        self.recording = True
        self.__start_time = time.time()
        print("Starting to record")

    def stop_recording(self) -> None:
        if not self.recording:
            raise Exception # TODO: find a proper exception or make one
        self.recording = False

        if self.__mouse_listener:
            self.__mouse_listener.stop()
        if self.__keyboard_listener:
            self.__keyboard_listener.stop()

        print(f"Stopped recording exporting the file to {self.output_file_path}")
        self.export_events()

    def export_events(self) -> None:
        with open(self.output_file_path, 'w') as file:
            json.dump([{"type": e.__class__.__name__, **e.model_dump()} for e in self.__events], file, indent=2)
        print(f"Recording saved to {self.output_file_path}")

    def __log_event(self, event: RecordingEvent) -> None:
        if not self.recording:
            raise Exception  # TODO: find a proper exception or make one

        event.time = time.time() - self.__start_time
        self.__events.append(event)

    def __on_click(self, x: int, y: int, button: Button, pressed: bool) -> None:
        if not self.recording:
            return None
        self.__log_event(MouseClickEvent(delta_x=x, delta_y=y, button=str(button), pressed=pressed))

    def __on_move(self, x: int, y: int) -> None:
        if not self.recording:
            return None

        if self.__last_mouse_position is None:
            self.__last_mouse_position = x, y

        last_x, last_y = self.__last_mouse_position
        dx, dy = x - last_x, y - last_y

        self.__last_mouse_position = (x, y)
        self.__log_event(MouseMoveEvent(delta_x=dx, delta_y=dy))

    def __on_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        if not self.recording:
            return None
        self.__log_event(MouseScrollEvent(delta_x=x, delta_y=y, scroll_dx=dx, scroll_dy=dy))

    def __on_press(self, key: Key) -> None:
        if key == self.start_recording_key and not self.recording:
            return self.start_recording()
        elif key == self.stop_recording_key and self.recording:
            return self.stop_recording()

        if not self.recording:
            return None
        self.__log_event(KeyPressEvent(key=str(key)))

    def __on_release(self, key: Key) -> None:
        if not self.recording or self.stop_recording_key or self.start_recording_key:
            return None
        self.__log_event(KeyReleaseEvent(key=str(key)))

    def run(self) -> None:
        print(f"Press {self.start_recording_key} to start recording")
        print(f"Press {self.stop_recording_key} to stop and export")
        self.__mouse_listener = mouse.Listener(
            on_click=self.__on_click,
            on_move=self.__on_move,
            on_scroll=self.__on_scroll)
        self.__keyboard_listener = keyboard.Listener(
            on_press=self.__on_press,
            on_release=self.__on_release)

        self.__mouse_listener.start()
        self.__keyboard_listener.start()
        self.__keyboard_listener.join()

if __name__ == "__main__":
    recorder = EventRecorder()
    recorder.run()