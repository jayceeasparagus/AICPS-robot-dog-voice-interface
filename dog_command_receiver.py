import argparse
import socket
import sys
import traceback


DEFAULT_HOST = "10.42.0.1"
DEFAULT_PORT = 5005
GO2_IFACE = "ethrobot"

VALID_COMMANDS = {
    "check",
    "stop",
    "stand",
    "sit",
    "stand_down",
}


def load_go2_client():
    from unitree_sdk2py.core.channel import ChannelFactoryInitialize
    from unitree_sdk2py.go2.sport.sport_client import SportClient

    ChannelFactoryInitialize(0, GO2_IFACE)

    client = SportClient()
    client.SetTimeout(3.0)
    client.Init()
    return client


def stop_motion(client):
    try:
        client.StopMove()
    except Exception as exc:
        print("Warning: StopMove failed:", exc)

    try:
        client.Move(0.0, 0.0, 0.0)
    except Exception as exc:
        print("Warning: zero Move failed:", exc)


def run_command(client, command):
    command = command.strip().lower()

    if command not in VALID_COMMANDS:
        return "ERROR invalid command: {}".format(command)

    if command == "check":
        print("Check command received.")
        return "OK check"

    if command == "stop":
        print("Stop command received.")
        stop_motion(client)
        return "OK stop"

    if command == "stand":
        print("Stand command received.")
        client.StandUp()
        return "OK stand"

    if command == "sit":
        print("Sit command received.")
        client.Sit()
        return "OK sit"

    if command == "stand_down":
        print("Stand down command received.")
        client.StandDown()
        return "OK stand_down"

    return "ERROR unreachable"


def handle_connection(conn, addr, client):
    try:
        data = conn.recv(1024)
        if not data:
            return

        command = data.decode("utf-8", errors="replace").strip().lower()
        print("Received from {}: {}".format(addr, command))

        response = run_command(client, command)
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
        description="Dog-side TCP receiver for Go2 posture commands."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--message-only",
        action="store_true",
        help="Receive and acknowledge commands without loading the Go2 SDK.",
    )
    args = parser.parse_args()

    client = None
    if args.message_only:
        print("Message-only mode enabled. This will not move the dog.")
    else:
        print("Initializing Go2 SportClient on {}.".format(GO2_IFACE))
        try:
            client = load_go2_client()
        except Exception:
            print("Failed to initialize Go2 client.")
            traceback.print_exc()
            sys.exit(1)
        print("Go2 SportClient ready.")

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
                handle_connection(conn, addr, client)
    except KeyboardInterrupt:
        print("\nStopping command receiver.")
    finally:
        if client is not None:
            stop_motion(client)
        server.close()


def handle_message_only_connection(conn, addr):
    try:
        data = conn.recv(1024)
        if not data:
            return

        command = data.decode("utf-8", errors="replace").strip().lower()
        print("Received from {}: {}".format(addr, command))

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
