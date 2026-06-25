import argparse
import socket
import sys


DEFAULT_HOST = "10.42.0.1"
DEFAULT_PORT = 5005
TIMEOUT_S = 2.0


def send_message(message, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=TIMEOUT_S):
    message = message.strip()
    if not message:
        raise ValueError("Message cannot be empty")

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall((message + "\n").encode("utf-8"))
        response = sock.recv(1024)

    return response.decode("utf-8", errors="replace").strip()


def main():
    parser = argparse.ArgumentParser(
        description="Test sender for SL1680 -> Go2 wired TCP messages."
    )
    parser.add_argument("message", help="Message text to send")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    try:
        response = send_message(args.message, host=args.host, port=args.port)
        print(response)
    except Exception as exc:
        print("SEND_ERROR:", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
