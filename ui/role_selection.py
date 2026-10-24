import tkinter as tk


class RoleSelectWindow:
    def __init__(self, root, on_choose):
        self.frame = tk.Frame(root, bg="#202124")
        self.frame.pack(fill="both", expand=True)
        tk.Label(self.frame, text="Выбери роль", fg="white", bg="#202124",
                 font=("Arial", 20, "bold")).pack(pady=(60, 30))
        self.bomb_btn = tk.Button(self.frame, text="Бомба", font=("Arial", 16, "bold"),
                                  width=20, height=2, command=lambda: on_choose("bomb"))
        self.bomb_btn.pack(pady=10)
        self.buttons_btn = tk.Button(self.frame, text="Кнопки", font=("Arial", 16, "bold"),
                                     width=20, height=2, command=lambda: on_choose("buttons"))
        self.buttons_btn.pack(pady=10)
        self.status = tk.Label(self.frame, text="", fg="#9aa0a6", bg="#202124",
                               font=("Arial", 12))
        self.status.pack(pady=20)

    def set_status(self, text):
        self.status.config(text=text)

    def set_role_busy(self, role, busy):
        button = self.bomb_btn if role == "bomb" else self.buttons_btn
        button.config(state="disabled" if busy else "normal")

    def destroy(self):
        self.frame.destroy()
