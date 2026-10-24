import tkinter as tk

from config import COLOR_HEX, TEXT_COLOR


class ButtonsScreen:
    def __init__(self, root, state, on_cut, on_role_reset, on_close):
        self.root = root
        self.state = state
        self.on_cut = on_cut
        self.on_role_reset = on_role_reset
        self.last_sig = None
        self.window = tk.Toplevel(root)
        self.window.title("Пульт сапёра")
        self.window.geometry("560x600+10+10")
        self.window.configure(bg="#202124")
        self.window.protocol("WM_DELETE_WINDOW", on_close)
        self.status_label = tk.Label(self.window, text="Ожидание бомбы...",
                                     fg="#9aa0a6", bg="#202124",
                                     font=("Arial", 13, "bold"), wraplength=520)
        self.status_label.pack(pady=(4, 10))
        self.role_btn = tk.Button(self.window, text="Сменить роль", font=("Arial", 12, "bold"),
                                  command=self.on_role_reset, state="disabled")
        self.role_btn.pack(pady=(0, 6))
        self.columns = tk.Frame(self.window, bg="#202124")
        columns = self.columns
        columns.pack(pady=4)
        left = tk.Frame(columns, bg="#202124")
        right = tk.Frame(columns, bg="#202124")
        left.grid(row=0, column=0, padx=14)
        right.grid(row=0, column=1, padx=14)
        tk.Label(left, text="ЛЕВАЯ СТОРОНА", fg="#9aa0a6", bg="#202124").pack()
        tk.Label(right, text="ПРАВАЯ СТОРОНА", fg="#9aa0a6", bg="#202124").pack()
        self.buttons = {}
        for n in range(10):
            parent = left if n < 5 else right
            b = tk.Button(parent, text=str(n), width=15, height=2,
                          font=("Arial", 14, "bold"), state="disabled",
                          disabledforeground="#777777", bg="#3c4043",
                          command=lambda k=n: self.on_cut(k))
            b.pack(pady=5)
            self.buttons[n] = b
        self.loop()

    def loop(self):
        snap = self.state.snapshot()
        sig = (snap["status"], snap["serial"], tuple(snap["cut"] or []))
        if sig != self.last_sig:
            self.last_sig = sig
            self.apply_state(snap)
        self.window.after(200, self.loop)

    def apply_state(self, snap):
        status = snap["status"]
        serial = snap["serial"]
        wires = snap["wires"]
        cut = set(snap["cut"] or [])
        running = status == "running"
        for n, b in self.buttons.items():
            if not wires:
                b.config(text=str(n), state="disabled", bg="#3c4043", fg="white")
                continue
            wire = next((w for w in wires if w["number"] == n), None)
            if wire is None:
                b.config(text=str(n), state="disabled", bg="#3c4043", fg="white")
                continue
            color = wire["color"]
            if n in cut:
                b.config(text=f"{n}  {color}\n(перерезан)", state="disabled",
                         bg="#3c4043", fg="white")
            else:
                b.config(text=f"{n}  {color}", bg=COLOR_HEX[color],
                         fg=TEXT_COLOR[color], activebackground=COLOR_HEX[color],
                         state="normal" if running else "disabled")
        if running:
            if self.role_btn.winfo_manager():
                self.role_btn.pack_forget()
        else:
            if not self.role_btn.winfo_manager():
                self.role_btn.pack(before=self.columns, pady=(0, 6))
            self.role_btn.config(state="normal")
        if status == "waiting":
            self.status_label.config(text="Ожидание старта бомбы...", fg="#9aa0a6")
        elif running:
            self.status_label.config(text="Бомба активна!", fg="#fdd835")
        elif status == "defused":
            self.status_label.config(text="БОМБА ОБЕЗВРЕЖЕНА!", fg="#35e06a")
        elif status == "exploded":
            self.status_label.config(text="ВЗРЫВ! " + snap.get("message", ""), fg="#ff5252")
