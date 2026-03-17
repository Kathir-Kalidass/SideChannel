#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class ChannelHandler(BaseHTTPRequestHandler):
    role = "channel"
    port = 0

    def do_GET(self) -> None:  # noqa: N802
        if self.path not in {"/", "/health"}:
            self.send_response(404)
            self.end_headers()
            return

        payload = {
            "status": "ok",
            "role": self.role,
            "port": self.port,
            "message": f"{self.role} channel is active",
        }
        body = json.dumps(payload).encode("utf-8")

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: object) -> None:
        return


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run simulated channel node")
    parser.add_argument("--role", required=True, choices=["sender", "receiver", "attacker"])
    parser.add_argument("--port", required=True, type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ChannelHandler.role = args.role
    ChannelHandler.port = args.port
    server = ThreadingHTTPServer(("0.0.0.0", args.port), ChannelHandler)
    print(f"{args.role} channel listening on port {args.port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
