import argparse
import os
import socket
import sys

from dog_command_protocol import (
    VALID_COMMANDS,
    build_command_message,
    encode_message,
    validate_command,
)


DEFAULT_HOST = os.environ.get("DOG_HOST", "192.168.123.46")
DEFAULT_PORT = 5005
TIMEOUT_S = 2.0


def send_command(
    command,
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
    timeout=TIMEOUT_S,
    source="manual",
    doa_deg=None,
    confidence=None,
    phrase=None,
):
    command = validate_command(command)
    message = build_command_message(
        command,
        source=source,
        doa_deg=doa_deg,
        confidence=confidence,
        phrase=phrase,
    )

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(encode_message(message))
        response = sock.recv(1024)

    return response.decode("utf-8", errors="replace").strip()


def main():
    parser = argparse.ArgumentParser(
        description="Board-side wireless sender for Go2 voice commands."
    )
    parser.add_argument("command", choices=sorted(VALID_COMMANDS))
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    try:
        response = send_command(args.command, host=args.host, port=args.port)
        print(response)
    except Exception as exc:
        print("SEND_ERROR:", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
