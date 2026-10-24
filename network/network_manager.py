import json
import queue
import socket
import threading
import time
import uuid

from config import UDP_PORT, BROADCAST_ADDR, HEARTBEAT_INTERVAL


class UdpBroadcast:
    def __init__(self):
        self.instance_id = uuid.uuid4().hex
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.bind(("", UDP_PORT))
        self.sock.settimeout(0.5)
        self.inbox = queue.Queue()
        self.running = True
        self.peer_last_seen = 0.0
        self.peer_role = None
        self.peer_claimed_role = None
        self.peer_addr = None
        self.own_role = None
        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()

    def send(self, packet_type, **fields):
        payload = {"type": packet_type, "sender": self.instance_id}
        payload.update(fields)
        try:
            data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            if packet_type != "HELLO" and self.peer_addr is not None:
                self.sock.sendto(data, self.peer_addr)
            else:
                self.sock.sendto(data, (BROADCAST_ADDR, UDP_PORT))
        except OSError:
            pass

    def peer_alive(self):
        return (time.monotonic() - self.peer_last_seen) < 2.0

    def close(self):
        self.running = False
        try:
            self.sock.close()
        except OSError:
            pass

    def _heartbeat_loop(self):
        while self.running:
            self.send("HELLO", role=self.own_role)
            time.sleep(HEARTBEAT_INTERVAL)

    def _recv_loop(self):
        while self.running:
            try:
                data, _addr = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                packet = json.loads(data.decode("utf-8"))
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(packet, dict) or "type" not in packet:
                continue
            if packet.get("sender") == self.instance_id:
                continue
            if packet["type"] == "HELLO":
                self.peer_last_seen = time.monotonic()
                self.peer_role = packet.get("role")
                self.peer_addr = _addr
                continue
            self.peer_addr = _addr
            self.inbox.put(packet)
