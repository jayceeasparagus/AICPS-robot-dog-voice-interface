import argparse
import socket
import sys


DEFAULT_HOST = "10.42.0.1"
DEFAULT_PORT = 5005
TIMEOUT_S = 2.0

VALID_COMMANDS = {
    "check",
    "stop",
    "stand",
    "sit",
    "stand_down",
}


def send_command(command, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=TIMEOUT_S):
    command = command.strip().lower()
    if command not in VALID_COMMANDS:
        raise ValueError(
            "Invalid command '{}'. Valid commands: {}".format(
                command, ", ".join(sorted(VALID_COMMANDS))
            )
        )

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall((command + "\n").encode("utf-8"))
        response = sock.recv(1024)

    return response.decode("utf-8", errors="replace").strip()


def main():
    parser = argparse.ArgumentParser(
        description="Board-side sender for Go2 posture commands."
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
