"""Serve a phone controller on the local network and relay commands to Ameba USB serial.

Run: python mobile_bridge.py --port COM3
The phone and PC must be on the same local network. Keep this process running.
"""

import argparse
import json
import re
import secrets
import socket
import threading
import time
import unicodedata
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import serial


ROOT = Path(__file__).resolve().parent / "mobile"
COMMANDS = {"左邊開燈": "LEFT", "右邊開燈": "RIGHT", "閃爍三次": "BLINK3", "閃爍3次": "BLINK3"}
REPLY = re.compile(r"^ACK ([1-9]\d{0,5}) BLUE=([01]) GREEN=([01])$")
ERROR = re.compile(r"^ERR ([1-9]\d{0,5}) (.+)$")


def parse_text(text):
    if not isinstance(text, str):
        return None
    cleaned = "".join(char for char in text if not char.isspace() and unicodedata.category(char)[0] not in "PS")
    return COMMANDS.get(cleaned, "OFF") if text.strip() else None


class SerialBridge:
    def __init__(self, port_name):
        self.port_name = port_name
        self.connection = None
        self.lock = threading.Lock()
        self.sequence = 0

    def close(self):
        if self.connection:
            try:
                self.connection.close()
            finally:
                self.connection = None

    def transact(self, action):
        with self.lock:
            try:
                if not self.connection or not self.connection.is_open:
                    self.connection = serial.Serial(self.port_name, 115200, timeout=0.2, write_timeout=2)
                    time.sleep(1.5)  # Let the board finish any reset triggered by opening COM.
                self.sequence = (self.sequence % 999999) + 1
                request_id = self.sequence
                self.connection.write(f"CMD {request_id} {action}\n".encode("ascii"))
                deadline = time.monotonic() + 5
                while time.monotonic() < deadline:
                    line = self.connection.readline().decode("ascii", errors="ignore").strip()
                    ack = REPLY.fullmatch(line)
                    if ack and int(ack.group(1)) == request_id:
                        return {"blue": ack.group(2) == "1", "green": ack.group(3) == "1"}
                    error = ERROR.fullmatch(line)
                    if error and int(error.group(1)) == request_id:
                        raise RuntimeError(f"板卡拒絕指令：{error.group(2)}")
                raise TimeoutError("板卡五秒內沒有回覆，請檢查韌體與 COM 埠")
            except (serial.SerialException, OSError):
                self.close()
                raise


def local_wifi_address():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("192.0.2.1", 1))
            return probe.getsockname()[0]
    except OSError:
        return "<電腦的 Wi-Fi IP>"


def make_handler(bridge, pairing_code):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format_string, *args):
            print(f"{self.client_address[0]} - {format_string % args}")

        def respond(self, status, data):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            assets = {
                "/": ("index.html", "text/html; charset=utf-8"),
                "/app.js": ("app.js", "text/javascript; charset=utf-8"),
                "/style.css": ("style.css", "text/css; charset=utf-8"),
            }
            asset = assets.get(self.path)
            if not asset:
                self.send_error(404)
                return
            content = (ROOT / asset[0]).read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", asset[1])
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)

        def do_POST(self):
            if self.path != "/api/command":
                self.respond(404, {"error": "找不到此功能"})
                return
            if not secrets.compare_digest(self.headers.get("X-Pairing-Code", ""), pairing_code):
                self.respond(403, {"error": "配對碼錯誤"})
                return
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if size < 1 or size > 2048:
                    raise ValueError("請輸入簡短指令")
                payload = json.loads(self.rfile.read(size))
                action = parse_text(payload.get("text")) if isinstance(payload, dict) else None
                if not action:
                    self.respond(422, {"error": "沒有收到語音或文字；未傳送指令"})
                    return
                state = bridge.transact(action)
                self.respond(200, {"action": action, **state})
            except (ValueError, json.JSONDecodeError) as error:
                self.respond(400, {"error": str(error)})
            except (serial.SerialException, OSError, TimeoutError, RuntimeError) as error:
                self.respond(503, {"error": f"通訊失敗：{error}"})

    return Handler


def main():
    parser = argparse.ArgumentParser(description="AMB82-MINI 手機控制橋接服務")
    parser.add_argument("--port", default="COM3", help="板卡的序列埠，預設 COM3")
    parser.add_argument("--listen-port", type=int, default=8765, help="手機連線的 HTTP 埠，預設 8765")
    args = parser.parse_args()
    pairing_code = f"{secrets.randbelow(1_000_000):06d}"
    bridge = SerialBridge(args.port)
    server = ThreadingHTTPServer(("0.0.0.0", args.listen_port), make_handler(bridge, pairing_code))
    print(f"板卡序列埠：{args.port}", flush=True)
    print(f"手機網址：http://{local_wifi_address()}:{args.listen_port}/", flush=True)
    print(f"本次配對碼：{pairing_code}", flush=True)
    print("請保持這個視窗開啟；手機與電腦需連到同一個 Wi-Fi。", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        bridge.close()


if __name__ == "__main__":
    main()
