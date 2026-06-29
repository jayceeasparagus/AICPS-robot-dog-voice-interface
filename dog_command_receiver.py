import argparse
from pathlib import Path
import socket
import subprocess
import traceback

from dog_command_protocol import VALID_COMMANDS, parse_command_message


DEFAULT_HOST = "10.42.0.1"
DEFAULT_PORT = 5005
GO2_COMMAND_SCRIPT = Path(__file__).resolve().parent / "go2_test_cmd.py"


def run_command(command):
    print("Running Go2 command:", command)
    result = subprocess.run(
        ["python3", str(GO2_COMMAND_SCRIPT), command],
        capture_output=True,
        text=True,
    )

    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, end="")

    if result.returncode != 0:
        return "ERROR {} returncode {}".format(command, result.returncode)

    return "OK {}".format(command)


def handle_connection(conn, addr):
    try:
        data = conn.recv(1024)
        if not data:
            return

        text = data.decode("utf-8", errors="replace")
        message = parse_command_message(text)
        command = message["command"]
        print("Received from {}: {}".format(addr, message))

        response = run_command(command)
        conn.sendall((response + "\n").encode("utf-8"))

    except Exception:
        traceback.print_exc()
        try:
            conn.sendall(b"ERROR server exception\n")
        except Exception:
            pass
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Dog-side TCP receiver for Go2 voice commands."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--message-only",
        action="store_true",
        help="Receive and acknowledge commands without loading the Go2 SDK.",
    )
    args = parser.parse_args()

    if args.message_only:
        print("Message-only mode enabled. This will not move the dog.")
    else:
        print("Command mode enabled. Commands run through go2_test_cmd.py.")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.host, args.port))
    server.listen(5)

    print("Command receiver listening on {}:{}.".format(args.host, args.port))
    print("Valid commands:", ", ".join(sorted(VALID_COMMANDS)))

    try:
        while True:
            conn, addr = server.accept()
            if args.message_only:
                handle_message_only_connection(conn, addr)
            else:
                handle_connection(conn, addr)
    except KeyboardInterrupt:
        print("\nStopping command receiver.")
    finally:
        server.close()


def handle_message_only_connection(conn, addr):
    try:
        data = conn.recv(1024)
        if not data:
            return

        text = data.decode("utf-8", errors="replace")
        message = parse_command_message(text)
        command = message["command"]
        print("Received from {}: {}".format(addr, message))

        if command in VALID_COMMANDS:
            response = "OK message_only {}".format(command)
        else:
            response = "ERROR invalid command: {}".format(command)

        conn.sendall((response + "\n").encode("utf-8"))

    except Exception:
        traceback.print_exc()
        try:
            conn.sendall(b"ERROR server exception\n")
        except Exception:
            pass
    finally:
        conn.close()


if __name__ == "__main__":
    main()
