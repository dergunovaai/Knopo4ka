import math
import os
import time
import tkinter as tk
from tkinter import simpledialog

try:
    from PIL import Image, ImageTk
except ImportError:
    Image = ImageTk = None

from config import TIME_LIMIT, N_WIRES, COLOR_HEX, INSTRUCTIONS
from ui.widgets import WIN_W, WIN_H, BODY, MONO, wire_geometry
from utils.resources import play_mp3, play_mp3_sequence, resource_path


class BombScreen:
    def __init__(self, root, state, on_start, peer_alive, on_role_reset, on_close):
        self.root = root
        self.state = state
        self.on_start = on_start
        self.peer_alive = peer_alive
        self.on_role_reset = on_role_reset
        self.on_close = on_close
        self.last_sig = None
        self.last_scenario = None
        self.last_terminal_status = None
        self.explosion_photo = None
        self.timer_limit = TIME_LIMIT
        self.window = tk.Toplevel(root)
        self.window.title("БОМБА")
        icon_path = resource_path("c4_icon.ico")
        if os.path.isfile(icon_path):
            try:
                self.window.iconbitmap(icon_path)
            except tk.TclError:
                pass
        self.window.geometry(f"{WIN_W}x{WIN_H}+10+10")
        self.window.configure(bg="#161616")
        self.window.protocol("WM_DELETE_WINDOW", on_close)
        self.canvas = tk.Canvas(self.window, width=WIN_W, height=WIN_H,
                                bg="#161616", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.build_instruction_window()
        self.loop()

    def build_instruction_window(self):
        win = tk.Toplevel(self.root)
        self.instr = win
        win.title("Инструкция")
        win.geometry("660x720+730+10")
        win.protocol("WM_DELETE_WINDOW", self.on_close)
        bottom = tk.Frame(win)
        bottom.pack(side="bottom", fill="x")
        self.start_btn = tk.Button(bottom, text="Ждём подключения пульта...",
                                   font=("Arial", 14, "bold"), bg="#777777",
                                   fg="white", command=self.on_start, pady=8,
                                   state="disabled")
        self.start_btn.pack(fill="x", padx=10, pady=(8, 4))
        self.timer_btn = tk.Button(bottom, text="Время: 120 сек. (2 минуты) — изменить",
                                   font=("Arial", 11, "bold"), command=self.choose_timer)
        self.timer_btn.pack(fill="x", padx=10, pady=(0, 4))
        self.role_btn = tk.Button(bottom, text="Сменить роль", font=("Arial", 12, "bold"),
                                  command=self.on_role_reset, state="disabled")
        self.role_btn.pack(fill="x", padx=10, pady=(0, 8))
        frame = tk.Frame(win)
        frame.pack(side="top", fill="both", expand=True)
        scroll = tk.Scrollbar(frame)
        scroll.pack(side="right", fill="y")
        self.text = tk.Text(frame, wrap="word", yscrollcommand=scroll.set,
                            padx=14, pady=10, font=("Arial", 11), bg="#fbfbf7",
                            cursor="arrow")
        self.text.pack(side="left", fill="both", expand=True)
        scroll.config(command=self.text.yview)
        self.text.tag_configure("title", font=("Arial", 16, "bold"), spacing3=8)
        self.text.config(state="disabled")

    def choose_timer(self):
        if self.state.snapshot()["status"] == "running":
            return
        value = simpledialog.askinteger(
            "Время таймера",
            "Введи время игры в секундах (по умолчанию 120):",
            parent=self.instr,
            initialvalue=self.timer_limit,
            minvalue=1,
            maxvalue=600,
        )
        if value is not None:
            self.timer_limit = value
            minutes, seconds = divmod(value, 60)
            self.timer_btn.config(text=f"Время: {value} сек. ({minutes}:{seconds:02d}) — изменить")

    def update_instruction(self, scenario):
        if scenario == self.last_scenario:
            return
        self.last_scenario = scenario
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        if scenario and scenario in INSTRUCTIONS:
            info = INSTRUCTIONS[scenario]
            self.text.insert("end", info["title"] + "\n", "title")
            self.text.insert("end", info["text"] + "\n")
        else:
            self.text.insert("end", "Инструкция появится после старта игры.\n")
        self.text.config(state="disabled")

    def loop(self):
        snap = self.state.snapshot()
        self.update_instruction(snap["scenario"])
        status = snap["status"]
        if status in ("exploded", "defused") and status != self.last_terminal_status:
            self.last_terminal_status = status
            if status == "exploded":
                play_mp3(resource_path("terrorists-win.mp3"))
            else:
                play_mp3_sequence([
                    resource_path("bomb-has-been-defused-csgo-sound-effect.mp3"),
                    resource_path("counter-terrorists-win.mp3"),
                ])
        if status == "waiting":
            self.last_terminal_status = None
        alive = self.peer_alive()
        if status == "waiting":
            if alive:
                self.start_btn.config(text="Принять и начать игру", state="normal", bg="#2e9e44")
            else:
                self.start_btn.config(text="Ждём подключения пульта...", state="disabled", bg="#777777")
        elif status == "running":
            self.start_btn.config(text="Игра идёт...", state="disabled", bg="#777777")
        elif alive:
            self.start_btn.config(text="Новая игра (принять и начать)", state="normal", bg="#2e9e44")
        else:
            self.start_btn.config(text="Ждём подключения пульта...", state="disabled", bg="#777777")
        # Hide the role-switch button only while the timer is running.
        if status == "running":
            if self.role_btn.winfo_manager():
                self.role_btn.pack_forget()
        else:
            if not self.role_btn.winfo_manager():
                self.role_btn.pack(fill="x", padx=10, pady=(0, 8))
            self.role_btn.config(state="normal")
        secs = math.ceil(snap["remaining"])
        flash = int(time.monotonic() * 3) % 2 if status == "exploded" else 0
        blink = secs % 2 if status == "running" and secs <= 10 else 0
        sig = (status, secs, tuple(snap["cut"]), flash, blink, snap["serial"])
        if sig != self.last_sig:
            self.last_sig = sig
            self.draw(snap, secs, flash, blink)
        self.window.after(100, self.loop)

    def draw(self, snap, secs, flash, blink):
        c = self.canvas
        c.delete("all")
        status = snap["status"]
        exploded = status == "exploded"
        bg = ("#ff3d00" if flash else "#8b0000") if exploded else "#161616"
        c.create_rectangle(0, 0, WIN_W, WIN_H, fill=bg, outline="")

        x0, y0, x1, y1 = BODY
        c.create_rectangle(x0, y0, x1, y1, fill="#3a3a3a", outline="#8a8a8a", width=4)
        c.create_rectangle(x0 + 10, y0 + 10, x1 - 10, y1 - 10, outline="#555555")

        c.create_rectangle(245, 40, 455, 130, fill="black", outline="#8a8a8a", width=3)
        if status == "waiting":
            limit = snap.get("timer_limit", TIME_LIMIT)
            shown, color = f"{limit // 60:02d}:{limit % 60:02d}", "#552222"
        else:
            shown = f"{secs // 60:02d}:{secs % 60:02d}"
            color = "#ff2a2a"
            if status == "defused":
                color = "#35e06a"
            elif blink:
                color = "#ffffff"
        c.create_text(350, 85, text=shown, fill=color, font=(MONO, 44, "bold"))

        serial_text = snap["serial"] if snap["serial"] else "C-?????"
        c.create_text(350, 155, text=serial_text, fill="#ffffff",
                      font=(MONO, 22, "bold"))

        if status == "waiting":
            c.create_text(350, 200, text="Прочитай инструкцию\nи нажми «Принять»",
                          fill="#aaaaaa", font=("Arial", 12), justify="center")
        elif status == "defused":
            c.create_text(350, 200, text="ОБЕЗВРЕЖЕНА!", fill="#35e06a",
                          font=("Arial", 22, "bold"))
        elif exploded:
            c.create_text(350, 195, text="БУМ!", fill="#ffffff",
                          font=("Arial", 40, "bold"))
            c.create_text(350, 235, text=snap["message"], fill="#ffffff",
                          font=("Arial", 13, "bold"))

        wires = snap["wires"]
        wires_by_number = {w["number"]: w for w in wires} if wires else {}
        for n in range(N_WIRES):
            side, y = wire_geometry(n)
            wire = wires_by_number.get(n)
            color_hex = COLOR_HEX[wire["color"]] if wire else "#4a4a4a"
            self.draw_wire(side, y, color_hex, n in snap["cut"])
            tx = 8 if side == "left" else WIN_W - 8
            anchor = "w" if side == "left" else "e"
            c.create_text(tx, y, text=str(n), fill="#ffffff",
                          font=("Arial", 15, "bold"), anchor=anchor)

        if exploded:
            cat_path = resource_path("cat_exploding.png")
            try:
                if os.path.isfile(cat_path):
                    if Image is not None and ImageTk is not None:
                        image = Image.open(cat_path).convert("RGBA")
                        self.explosion_photo = ImageTk.PhotoImage(image)
                    else:
                        self.explosion_photo = tk.PhotoImage(file=cat_path)
                    c.create_image(WIN_W // 2, WIN_H // 2 + 25,
                                   image=self.explosion_photo, anchor="center")
                else:
                    c.create_text(WIN_W // 2, WIN_H // 2 + 25,
                                  text="Не найден cat_exploding.png",
                                  fill="white", font=("Arial", 18, "bold"))
            except Exception:
                self.explosion_photo = None
                c.create_text(WIN_W // 2, WIN_H // 2 + 25,
                              text="Не удалось загрузить кота",
                              fill="white", font=("Arial", 12, "bold"))

        if status == "exploded":
            message = "GG"
        elif status == "defused":
            message = "GG WP"
        else:
            message = None
        if message:
            c.create_text(WIN_W // 2, 35, text=message, fill="white",
                          font=("Arial", 30, "bold"))

    def draw_wire(self, side, y, color_hex, is_cut):
        c = self.canvas
        if side == "left":
            segs = [(35, 100), (170, 215)] if is_cut else [(35, 215)]
        else:
            segs = [(485, 530), (600, 665)] if is_cut else [(485, 665)]
        for xa, xb in segs:
            c.create_line(xa, y, xb, y, width=16, fill="#0a0a0a", capstyle="round")
            c.create_line(xa, y, xb, y, width=10, fill=color_hex, capstyle="round")
        if is_cut:
            gx = 135 if side == "left" else 565
            c.create_text(gx, y, text="✂", fill="#ffffff", font=("Arial", 14))
