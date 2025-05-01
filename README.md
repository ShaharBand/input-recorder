# 🖱️ Computer Input Recorder & Player
A lightweight Python tool to record and replay mouse and keyboard events on your computer — ideal for automation, testing, or demonstrations.

### 📦 Features
- ⌨️ Records keyboard presses and releases
- 🖱️ Tracks mouse movements, clicks, and scrolls
- 📁 Saves recordings in JSON format
- 🔁 Replays input events accurately
- ✅ Typed event structure using Pydantic
 
### 🚀 Getting Started
#### Install the environment
Make sure uv is installed:
```shell
curl -Ls https://astral.sh/uv/install.sh | sh
```

#### 🎥 Recording Input Events
To start recording mouse and keyboard input:
```python
uv run python .\event_recorder.py
``` 

#### 🔁 Replaying Input Events
To replay previously recorded events:
```python
uv run python .\event_player.py
```


### ⚠️ Notes
The overlay feature is currently under development and excluded from this version.