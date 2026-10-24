import threading
import time

from config import TIME_LIMIT
from game.logic import new_serial, new_wires, pick_scenario, correct_cut, total_cuts_needed


class GameState:
    def __init__(self):
        self.lock = threading.RLock()
        self.status = "waiting"
        self.serial = None
        self.wires = None
        self.scenario = None
        self.cut = []
        self.fallback_count = 0
        self.end_time = 0.0
        self.final_remaining = float(TIME_LIMIT)
        self.timer_limit = TIME_LIMIT
        self.message = ""

    def start(self, timer_limit=TIME_LIMIT):
        with self.lock:
            self.serial = new_serial()
            self.wires = new_wires()
            self.scenario = pick_scenario()
            self.cut = []
            self.fallback_count = 0
            self.message = ""
            self.timer_limit = max(1, int(timer_limit))
            self.final_remaining = float(self.timer_limit)
            self.end_time = time.monotonic() + self.timer_limit
            self.status = "running"

    def start_time_from_remote(self, timer_limit=TIME_LIMIT):
        with self.lock:
            self.cut = []
            self.fallback_count = 0
            self.message = ""
            self.timer_limit = max(1, int(timer_limit))
            self.final_remaining = float(self.timer_limit)
            self.end_time = time.monotonic() + self.timer_limit
            self.status = "running"

    def _tick(self):
        if self.status == "running" and time.monotonic() >= self.end_time:
            self.status = "exploded"
            self.final_remaining = 0.0
            self.message = "Время вышло!"

    def cut_wire(self, number):
        with self.lock:
            self._tick()
            if self.status != "running":
                return self.status
            if number in self.cut:
                return "already_cut"
            allowed, new_fallback = correct_cut(
                self.scenario, self.serial, self.wires, self.cut, self.fallback_count
            )
            self.cut.append(number)
            self.final_remaining = max(0.0, self.end_time - time.monotonic())
            if number not in allowed:
                self.status = "exploded"
                self.message = f"Провод №{number} — неверный!"
                return self.status
            self.fallback_count = new_fallback
            if len(self.cut) >= total_cuts_needed(self.serial):
                self.status = "defused"
            return self.status

    def snapshot(self):
        with self.lock:
            self._tick()
            if self.status == "running":
                remaining = max(0.0, self.end_time - time.monotonic())
            else:
                remaining = self.final_remaining
            return {
                "status": self.status,
                "message": self.message,
                "remaining": remaining,
                "timer_limit": self.timer_limit,
                "serial": self.serial,
                "wires": list(self.wires) if self.wires else None,
                "scenario": self.scenario,
                "cut": list(self.cut),
            }
