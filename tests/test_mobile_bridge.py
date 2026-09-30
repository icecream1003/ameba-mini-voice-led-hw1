import http.client
import json
import threading
import unittest
from http.server import ThreadingHTTPServer

from mobile_bridge import SerialBridge, make_handler, parse_text


class FakeSerial:
    is_open = True

    def __init__(self):
        self.outgoing = []
        self.next_reply = b""

    def write(self, data):
        self.outgoing.append(data)
        request_id = data.decode("ascii").split()[1]
        self.next_reply = f"ACK {request_id} BLUE=1 GREEN=0\n".encode("ascii")

    def readline(self):
        reply = self.next_reply
        self.next_reply = b""
        return reply


class BridgeTests(unittest.TestCase):
    def test_exact_commands(self):
        self.assertEqual(parse_text("閃爍三次！"), "BLINK3")
        self.assertEqual(parse_text("左 邊 開 燈"), "LEFT")
        self.assertEqual(parse_text("請幫我左邊開燈"), "OFF")
        self.assertIsNone(parse_text("  "))

    def test_serial_protocol(self):
        bridge = SerialBridge("COM3")
        fake = FakeSerial()
        bridge.connection = fake
        self.assertEqual(bridge.transact("BLINK3"), {"blue": True, "green": False})
        self.assertEqual(fake.outgoing, [b"CMD 1 BLINK3\n"])

    def test_http_sends_off_for_unknown_and_rejects_empty_or_wrong_pin(self):
        bridge = SerialBridge("COM3")
        fake = FakeSerial()
        bridge.connection = fake
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(bridge, "123456"))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            connection = http.client.HTTPConnection("127.0.0.1", server.server_port)
            for pin, text, expected in [
                ("wrong", "左邊開燈", 403),
                ("123456", "", 422),
                ("123456", "今天天氣很好", 200),
                ("123456", "右邊開燈", 200),
            ]:
                connection.request("POST", "/api/command", json.dumps({"text": text}), {
                    "Content-Type": "application/json", "X-Pairing-Code": pin
                })
                response = connection.getresponse()
                self.assertEqual(response.status, expected)
                response.read()
            self.assertEqual(fake.outgoing, [b"CMD 1 OFF\n", b"CMD 2 RIGHT\n"])
            connection.close()
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
