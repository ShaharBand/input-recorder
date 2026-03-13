import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from event import ImageClickEvent


def ask_mouse_position(
    root: tk.Tk,
    initial: tuple[int, int] | None = None,
) -> tuple[int, int] | None: 
    win = tk.Toplevel(root)
    win.title("Mouse Position")
    win.transient(root)
    win.resizable(False, False)

    x_default = initial[0] if initial is not None else 0
    y_default = initial[1] if initial is not None else 0

    tk.Label(win, text="X:").grid(row=0, column=0, padx=8, pady=6, sticky="e")
    x_var = tk.IntVar(value=x_default)
    tk.Entry(win, textvariable=x_var, width=10).grid(row=0, column=1, padx=8, pady=6)

    tk.Label(win, text="Y:").grid(row=1, column=0, padx=8, pady=6, sticky="e")
    y_var = tk.IntVar(value=y_default)
    tk.Entry(win, textvariable=y_var, width=10).grid(row=1, column=1, padx=8, pady=6)

    result: tuple[int, int] | None = None

    def on_ok() -> None:
        nonlocal result
        try:
            x_val = int(x_var.get())
            y_val = int(y_var.get())
        except (TypeError, ValueError):
            messagebox.showerror("Invalid input", "X and Y must be integers.")
            return
        if x_val < 0 or y_val < 0:
            messagebox.showerror("Invalid input", "Coordinates must be ≥ 0.")
            return
        result = (x_val, y_val)
        win.destroy()

    def on_cancel() -> None:
        win.destroy()

    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=2, column=0, columnspan=2, pady=(4, 8))
    ttk.Button(btn_frame, text="OK", command=on_ok).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)

    win.grab_set()
    root.wait_window(win)
    return result


def ask_image_event(
    root: tk.Tk,
    initial: ImageClickEvent | None = None,
) -> ImageClickEvent | None: 
    win = tk.Toplevel(root)
    win.title("Add Click Image")
    win.transient(root)
    win.resizable(False, False)

    # Image path + browse
    tk.Label(win, text="Image file:").grid(row=0, column=0, padx=8, pady=6, sticky="e")
    path_var = tk.StringVar(value=initial.image_path if initial is not None else "")
    path_entry = tk.Entry(win, textvariable=path_var, width=40)
    path_entry.grid(row=0, column=1, padx=4, pady=6, sticky="w")

    def browse() -> None:
        path = filedialog.askopenfilename(
            title="Select image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp")],
        )
        if path:
            path_var.set(path)

    ttk.Button(win, text="Browse…", command=browse).grid(row=0, column=2, padx=4, pady=6)

    # Button (left/right)
    tk.Label(win, text="Button:").grid(row=1, column=0, padx=8, pady=6, sticky="e")
    button_var = tk.StringVar(value=initial.button if initial is not None else "left")
    ttk.Combobox(
        win,
        textvariable=button_var,
        values=["left", "right"],
        width=10,
        state="readonly",
    ).grid(row=1, column=1, padx=4, pady=6, sticky="w")

    # Confidence
    tk.Label(win, text="Confidence:").grid(row=2, column=0, padx=8, pady=6, sticky="e")
    conf_var = tk.DoubleVar(value=initial.confidence if initial is not None else 0.85)
    tk.Entry(win, textvariable=conf_var, width=10).grid(row=2, column=1, padx=4, pady=6, sticky="w")

    # Timeout
    tk.Label(win, text="Timeout (s):").grid(row=3, column=0, padx=8, pady=6, sticky="e")
    timeout_var = tk.DoubleVar(
        value=initial.timeout_seconds if initial is not None else 30.0
    )
    tk.Entry(win, textvariable=timeout_var, width=10).grid(row=3, column=1, padx=4, pady=6, sticky="w")

    # Fail action
    tk.Label(win, text="On failure:").grid(row=4, column=0, padx=8, pady=6, sticky="e")
    fail_var = tk.StringVar(value=initial.fail_action if initial is not None else "skip")
    ttk.Combobox(
        win,
        textvariable=fail_var,
        values=["skip", "stop"],
        width=10,
        state="readonly",
    ).grid(row=4, column=1, padx=4, pady=6, sticky="w")

    result: ImageClickEvent | None = None

    def on_ok() -> None:
        nonlocal result
        path = path_var.get().strip()
        if not path:
            messagebox.showerror("Missing image", "Please choose an image file.")
            return
        try:
            conf_val = float(conf_var.get())
            timeout_val = float(timeout_var.get())
        except (TypeError, ValueError):
            messagebox.showerror("Invalid input", "Confidence and timeout must be numbers.")
            return
        if not (0.6 <= conf_val <= 1.0):
            messagebox.showerror("Invalid confidence", "Confidence must be between 0.6 and 1.0.")
            return
        if timeout_val <= 0:
            messagebox.showerror("Invalid timeout", "Timeout must be greater than 0.")
            return

        button = button_var.get() or "left"
        fail_action = fail_var.get() or "skip"
        result = ImageClickEvent(
            image_path=path,
            button=button,
            confidence=conf_val,
            timeout_seconds=timeout_val,
            grayscale=True,
            fail_action=fail_action,  # type: ignore[arg-type]
        )
        win.destroy()

    def on_cancel() -> None:
        win.destroy()

    btn_frame = ttk.Frame(win)
    btn_frame.grid(row=5, column=0, columnspan=3, pady=(4, 8))
    ttk.Button(btn_frame, text="OK", command=on_ok).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="Cancel", command=on_cancel).pack(side="left", padx=5)

    win.grab_set()
    root.wait_window(win)
    return result


