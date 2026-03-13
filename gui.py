import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from pathlib import Path

from player import EventPlayer
from recorder import EventRecorder
from pynput.keyboard import Key
from event import (
    RecordingEvent,
    WaitEvent,
    ImageClickEvent,
    RunRecordingEvent,
    KeyPressEvent,
    MouseClickEvent,
    MousePositionEvent,
)
from dialogs import ask_mouse_position, ask_image_event


class RecipeBuilder:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Macro Manager GUI")
        self.root.geometry("1400x1000")

        self.recipe: list[RecordingEvent] = []
        self.speed_multiplier: float = 1.0
        self.non_wait_gap: float = 0.5
        self.repeat_count: int = 1
        self.recorder: EventRecorder | None = None 
        self.rec_start_hotkey: str = "F7"
        self.rec_stop_hotkey: str = "F7"

        self._build_ui()

    def _build_ui(self) -> None:
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill="x", padx=10, pady=5)

        ttk.Button(toolbar, text="New", command=self.new_recipe).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Load", command=self.load_recipe).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Save", command=self.save_recipe).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Run", command=self.run_recipe).pack(side="left", padx=10)

        ttk.Label(toolbar, text="Speed ×").pack(side="left", padx=5)
        self.speed_var = tk.DoubleVar(value=1.0)
        ttk.Spinbox(toolbar, from_=0.1, to=5.0, increment=0.1, textvariable=self.speed_var, width=6, command=self._update_speed).pack(side='left')

        ttk.Label(toolbar, text="Gap (s)").pack(side="left", padx=5)
        self.gap_var = tk.DoubleVar(value=self.non_wait_gap)
        ttk.Spinbox(toolbar, from_=0.0, to=10.0, increment=0.1, textvariable=self.gap_var, width=6, command=self._update_gap).pack(side='left')

        ttk.Label(toolbar, text="Repeat").pack(side="left", padx=(15, 5))
        self.repeat_var = tk.IntVar(value=self.repeat_count)
        ttk.Spinbox(
            toolbar,
            from_=1,
            to=999,
            increment=1,
            textvariable=self.repeat_var,
            width=4,
            command=self._update_repeat,
        ).pack(side="left")
 
        style = ttk.Style(self.root)
        style.configure(
            "Recipe.Treeview",
            rowheight=26,
            borderwidth=1,
            relief="solid",
        )

        self.tree = ttk.Treeview(
            self.root,
            columns=("event", "time", "info"),
            show="headings",
            selectmode="browse",
            height=24,
            style="Recipe.Treeview",
        )
        self.tree.heading("event", text="Event")
        self.tree.heading("time", text="Time (s)")
        self.tree.heading("info", text="Info")
        self.tree.column("event", width=180, anchor="w")
        self.tree.column("time", width=90, anchor="center")
        self.tree.column("info", width=460, anchor="w")
        self.tree.tag_configure("even", background="#f5f5f5")
        self.tree.tag_configure("odd", background="#ffffff")
        self.tree.pack(fill="both", expand=True, padx=10, pady=5)
 
        add_frame = ttk.LabelFrame(self.root, text="Add Event")
        add_frame.pack(fill="x", padx=10, pady=(0, 5))

        ttk.Button(add_frame, text="Add Wait", command=lambda: self.add_step("wait")).grid(row=0, column=0, padx=3, pady=3, sticky="ew")
        ttk.Button(add_frame, text="Add Play Recording", command=lambda: self.add_step("play")).grid(row=0, column=1, padx=3, pady=3, sticky="ew")
        ttk.Button(add_frame, text="Add Click Image", command=lambda: self.add_step("image")).grid(row=0, column=2, padx=3, pady=3, sticky="ew")
        
        ttk.Button(add_frame, text="Add Click Press", command=lambda: self.add_step("mouse_click")).grid(row=1, column=0, padx=3, pady=3, sticky="ew")
        ttk.Button(add_frame, text="Add Button Press", command=lambda: self.add_step("key")).grid(row=1, column=1, padx=3, pady=3, sticky="ew")
        ttk.Button(add_frame, text="Add Mouse Position", command=lambda: self.add_step("mouse_pos")).grid(row=1, column=2, padx=3, pady=3, sticky="ew")

        for col in range(3):
            add_frame.columnconfigure(col, weight=1)

 
        action_frame = ttk.Frame(self.root)
        action_frame.pack(fill="x", padx=10, pady=5)
 
        ttk.Button(action_frame, text="Start Rec", command=self.start_recording).pack(
            side="left", padx=3
        )
        ttk.Button(action_frame, text="Stop Rec", command=self.stop_recording).pack(
            side="left", padx=3
        )

        ttk.Label(action_frame, text="Start key").pack(side="left", padx=(15, 5))
        self.rec_start_hotkey_var = tk.StringVar(value=self.rec_start_hotkey)
        ttk.Combobox(
            action_frame,
            textvariable=self.rec_start_hotkey_var,
            values=[f"F{i}" for i in range(1, 13)],
            state="readonly",
            width=4,
        ).pack(side="left")

        ttk.Label(action_frame, text="Stop key").pack(side="left", padx=5)
        self.rec_stop_hotkey_var = tk.StringVar(value=self.rec_stop_hotkey)
        ttk.Combobox(
            action_frame,
            textvariable=self.rec_stop_hotkey_var,
            values=[f"F{i}" for i in range(1, 13)],
            state="readonly",
            width=4,
        ).pack(side="left")

        ttk.Button(action_frame, text="Edit", command=self.edit_step).pack(side="right", padx=3)
        ttk.Button(action_frame, text="Delete", command=self.delete_step).pack(side="right", padx=3)
        ttk.Button(action_frame, text="↑ Up", command=lambda: self.move_step(-1)).pack(side="right", padx=3)
        ttk.Button(action_frame, text="↓ Down", command=lambda: self.move_step(1)).pack(side="right", padx=3)

        self.tree.bind("<Double-1>", lambda _e: self.edit_step())

    def _update_speed(self) -> None:
        self.speed_multiplier = float(self.speed_var.get())

    def _update_gap(self) -> None:
        self.non_wait_gap = float(self.gap_var.get())

    def _update_repeat(self) -> None:
        try:
            value = int(self.repeat_var.get())
        except (TypeError, ValueError):
            value = 1
        if value < 1:
            value = 1
        self.repeat_count = value
        self.repeat_var.set(self.repeat_count)

    def start_recording(self) -> None:
        if self.recorder and self.recorder.recording:
            messagebox.showinfo("Recording", "Recording is already in progress.")
            return

        if self.recorder is None:
            # Map selected function keys (F1–F12) to pynput Key
            start_label = self.rec_start_hotkey_var.get() or "F7"
            stop_label = self.rec_stop_hotkey_var.get() or start_label
            fn_map: dict[str, Key] = {
                "F1": Key.f1,
                "F2": Key.f2,
                "F3": Key.f3,
                "F4": Key.f4,
                "F5": Key.f5,
                "F6": Key.f6,
                "F7": Key.f7,
                "F8": Key.f8,
                "F9": Key.f9,
                "F10": Key.f10,
                "F11": Key.f11,
                "F12": Key.f12,
            }
            start_key = fn_map.get(start_label, Key.f7)
            stop_key = fn_map.get(stop_label, start_key)
            self.rec_start_hotkey = start_label
            self.rec_stop_hotkey = stop_label

            self.recorder = EventRecorder(
                start_recording_key=start_key,
                stop_recording_key=stop_key,
            )
            
            self.recorder.on_stop = self._on_recorder_stopped
            self.recorder.setup_listeners()

            messagebox.showinfo(
                "Recorder armed",
                f"Listeners are running.\n"
                f"Press the start key ({self.rec_start_hotkey}) or click 'Start Rec' again to begin recording.",
            )
            return

        if not self.recorder.recording:
            self.recorder.start_recording()
            messagebox.showinfo(
                "Recording started",
                "Input recording has started.\n"
                "Use the Stop Rec button or the configured stop key to stop.",
            )

    def stop_recording(self) -> None:
        if not self.recorder or not self.recorder.recording:
            messagebox.showinfo("Recording", "No active recording to stop.")
            return

        self.recorder.stop_recording()

    def _on_recorder_stopped(self, recorder: EventRecorder) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
            title="Save recording as...",
        )
        if path:
            recorder.output_file_path = path
        recorder.export_events()
        if path:
            messagebox.showinfo("Recording saved", f"Recording saved to {path}")
        else:
            messagebox.showinfo(
                "Recording stopped",
                f"Recording stopped. Saved to default file: {recorder.output_file_path}",
            )
        self.recorder = None

    def _build_scheduled_events(self) -> list[RecordingEvent]:
        current_time = 0.0
        scheduled: list[RecordingEvent] = []
        for step in self.recipe:
            event = step.model_copy(deep=True)
            event.time = current_time
            if isinstance(event, WaitEvent):
                current_time += float(event.duration_seconds)
            else:
                current_time += self.non_wait_gap
            scheduled.append(event)
        return scheduled

    def _refresh_listbox(self) -> None:
        for item_id in self.tree.get_children():
            self.tree.delete(item_id)

        scheduled = self._build_scheduled_events()
        for idx, event in enumerate(scheduled):
            if isinstance(event, WaitEvent):
                event_name = "Wait"
                info = f"{event.duration_seconds} sec"
            elif isinstance(event, MousePositionEvent):
                event_name = "Mouse Position"
                info = f"({event.x}, {event.y})"
            elif isinstance(event, RunRecordingEvent):
                event_name = "Play Recording"
                info = Path(event.file_path).name
            elif isinstance(event, ImageClickEvent):
                event_name = "Click Image"
                info = f"{Path(event.image_path).name} (conf {event.confidence})"
            elif isinstance(event, KeyPressEvent):
                event_name = "Key Press"
                info = event.key
            elif isinstance(event, MouseClickEvent):
                state = "down" if event.pressed else "up"
                event_name = "Mouse Click"
                info = f"{event.button} ({state})"
            else:
                event_name = event.__class__.__name__
                info = ""

            time_str = f"{event.time:.2f}"
            tag = "even" if idx % 2 == 0 else "odd"
            self.tree.insert(
                "",
                "end",
                iid=str(idx),
                values=(event_name, time_str, info),
                tags=(tag,),
            )

    def add_step(self, kind: str) -> None:
        if kind == "wait":
            sec = simpledialog.askfloat(
                "Add Wait", "Duration (seconds):", minvalue=0.1, maxvalue=300
            )
            if sec is None:
                return
            self.recipe.append(WaitEvent(duration_seconds=float(sec)))

        elif kind == "play":
            path = filedialog.askopenfilename(
                title="Select recording JSON", filetypes=[("JSON", "*.json")]
            )
            if not path:
                return
            self.recipe.append(RunRecordingEvent(file_path=path, speed_multiplier=None))

        elif kind == "key":
            key = simpledialog.askstring("Key Press", "Key (e.g. 'a', 'Key.enter'):")
            if not key:
                return
            self.recipe.append(KeyPressEvent(key=key))

        elif kind == "mouse_click":
            button = simpledialog.askstring("Mouse Click", "Button (left / right):", initialvalue="left")
            if not button:
                return
            self.recipe.append(MouseClickEvent(button=button, pressed=True))

        elif kind == "mouse_pos":
            pos = ask_mouse_position(self.root)
            if pos is None:
                return
            x, y = pos
            self.recipe.append(MousePositionEvent(x=x, y=y))

        elif kind == "image":
            img_event = ask_image_event(self.root)
            if img_event is None:
                return
            self.recipe.append(img_event)

        self._refresh_listbox()

    def edit_step(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        step = self.recipe[idx]

        if isinstance(step, WaitEvent):
            new_d = simpledialog.askfloat(
                "Edit Wait", "New duration (s):", initialvalue=step.duration_seconds
            )
            if new_d is not None:
                step.duration_seconds = float(new_d)

        elif isinstance(step, MousePositionEvent):
            pos = ask_mouse_position(self.root, (step.x, step.y))
            if pos is not None:
                step.x, step.y = pos

        elif isinstance(step, ImageClickEvent):
            updated = ask_image_event(self.root, step)
            if updated is not None:
                self.recipe[idx] = updated

        elif isinstance(step, KeyPressEvent):
            key = simpledialog.askstring(
                "Edit Key Press", "Key (e.g. 'a', 'Key.enter'):", initialvalue=step.key
            )
            if key:
                step.key = key

        elif isinstance(step, MouseClickEvent):
            button = simpledialog.askstring(
                "Edit Mouse Click",
                "Button (left / right):",
                initialvalue=step.button,
            )
            if button:
                step.button = button

        elif isinstance(step, RunRecordingEvent):
            path = filedialog.askopenfilename(
                title="Select recording JSON", filetypes=[("JSON", "*.json")]
            )
            if path:
                step.file_path = path

        self._refresh_listbox()

    def delete_step(self) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        if messagebox.askyesno("Confirm", "Delete this step?"):
            idx = int(sel[0])
            del self.recipe[idx]
            self._refresh_listbox()

    def move_step(self, delta: int) -> None:
        sel = self.tree.selection()
        if not sel:
            return
        idx = int(sel[0])
        new_idx = idx + delta
        if 0 <= new_idx < len(self.recipe):
            self.recipe[idx], self.recipe[new_idx] = self.recipe[new_idx], self.recipe[idx]
            self._refresh_listbox()
            self.tree.selection_set(str(new_idx))

    def new_recipe(self) -> None:
        if self.recipe and messagebox.askyesno("New", "Discard current recipe?"):
            self.recipe = []
            self._refresh_listbox()

    def save_recipe(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON", "*.json")])
        if not path:
            return

        events = self._build_scheduled_events()
        payload = [
            {"type": event.__class__.__name__, **event.model_dump()}
            for event in events
        ]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        messagebox.showinfo("Saved", f"Saved to {path}")

    def load_recipe(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
 
            allowed_types = {
                "WaitEvent": WaitEvent,
                "ImageClickEvent": ImageClickEvent,
                "RunRecordingEvent": RunRecordingEvent,
                "KeyPressEvent": KeyPressEvent,
                "MouseClickEvent": MouseClickEvent,
                "MousePositionEvent": MousePositionEvent,
            }
            self.recipe = []
            for item in data:
                event_type = item.get("type")
                cls = allowed_types.get(event_type)
                if cls is not None:
                    self.recipe.append(cls.model_validate(item))

            self._refresh_listbox()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid recipe:\n{e}")

    def run_recipe(self) -> None:
        if not self.recipe:
            messagebox.showwarning("Empty", "No steps in recipe.")
            return

        repeat = max(1, int(self.repeat_var.get() or 1))

        for _ in range(repeat):
            events = self._build_scheduled_events()
            player = EventPlayer(speed_multiplier=self.speed_multiplier)
            player._EventPlayer__events = events
            player.start_playing()
            player._play_recording()
 
            if not player.playing:
                break

        messagebox.showinfo("Finished", f"Recipe playback completed (×{repeat}).")

if __name__ == "__main__":
    root = tk.Tk()
    app = RecipeBuilder(root)
    root.mainloop()