from pydantic import BaseModel, Field

class RecordingEvent(BaseModel):
    time: float = Field(default=0, ge=0)

class MouseEvent(RecordingEvent):
    delta_x: int = Field(default=0)
    delta_y: int = Field(default=0)

class MouseMoveEvent(MouseEvent):
    pass

class MouseClickEvent(MouseEvent):
    button: str
    pressed: bool = Field(default=False)

class MouseScrollEvent(MouseEvent):
    scroll_dx: int = Field(default=0)
    scroll_dy: int = Field(default=0)

class KeyEvent(RecordingEvent):
    key: str

class KeyPressEvent(KeyEvent):
    pass

class KeyReleaseEvent(KeyEvent):
    pass
