import argparse
import socket
import traceback


DEFAULT_HOST = "10.42.0.1"
DEFAULT_PORT = 5005


def handle_connection(conn, addr):
    try:
        data = conn.recv(1024)
        if not data:
            return

        message = data.decode("utf-8", errors="replace").strip()
        print("Received from {}: {}".format(addr, message))

        response = "OK received: {}".format(message)
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
        description="Test receiver for wired SL1680 -> Go2 TCP messages."
    )
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((args.host, args.port))
    server.listen(5)

    print("Test receiver listening on {}:{}.".format(args.host, args.port))
    print("This test receiver does not control the dog.")

    try:
        while True:
            conn, addr = server.accept()
            handle_connection(conn, addr)
    except KeyboardInterrupt:
        print("\nStopping test receiver.")
    finally:
        server.close()


if __name__ == "__main__":
    main()
