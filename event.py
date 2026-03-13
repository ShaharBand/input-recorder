from typing import Literal

from pydantic import BaseModel, Field

class RecordingEvent(BaseModel):
    time: float = Field(default=0, ge=0)

class MouseEvent(RecordingEvent):
    pass

class MouseMoveEvent(MouseEvent):
    delta_x: int = Field(default=0)
    delta_y: int = Field(default=0)

class MouseClickEvent(MouseEvent):
    button: str
    pressed: bool = Field(default=False)

class MouseScrollEvent(MouseEvent):
    scroll_dx: int = Field(default=0)
    scroll_dy: int = Field(default=0)

class MousePositionEvent(MouseEvent):
    x: int
    y: int

class KeyEvent(RecordingEvent):
    key: str

class KeyPressEvent(KeyEvent):
    pass

class KeyReleaseEvent(KeyEvent):
    pass

class WaitEvent(RecordingEvent):
    duration_seconds: float = Field(..., gt=0)

class ImageClickEvent(RecordingEvent):
    image_path: str
    button: str
    confidence: float = Field(0.85, ge=0.6, le=1.0)
    timeout_seconds: float | None = Field(30.0, ge=1.0)
    grayscale: bool = True
    fail_action: Literal["stop", "skip"] = "skip"

class RunRecordingEvent(RecordingEvent):
    file_path: str
    speed_multiplier: float | None = None
