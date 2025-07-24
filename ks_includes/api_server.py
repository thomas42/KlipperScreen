import json
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gi.repository import GLib


class APIRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/api/status":
            state = getattr(self.server.screen.printer, "state", "unknown")
            self._send_json({"status": state})
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path == "/api/restart":
            GLib.idle_add(self.server.screen.restart_ks)
            self._send_json({"result": "restarting"})
        elif self.path == "/api/reconnect":
            GLib.idle_add(self.server.screen.connect_to_moonraker)
            self._send_json({"result": "reconnecting"})
        else:
            self.send_error(404)

    def log_message(self, fmt, *args):
        logging.info("%s - %s" % (self.address_string(), fmt % args))


class APIServer(threading.Thread):
    def __init__(self, screen, host="0.0.0.0", port=3344):
        super().__init__(daemon=True)
        self.screen = screen
        self.server = ThreadingHTTPServer((host, port), APIRequestHandler)
        self.server.screen = screen

    def run(self):
        logging.info("API server listening on %s:%s", *self.server.server_address)
        try:
            self.server.serve_forever()
        except Exception as e:
            logging.exception(f"API server stopped: {e}")

    def stop(self):
        self.server.shutdown()
