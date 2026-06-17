import os
import socket

os.environ.setdefault('FLASK_ENV', 'development')

from app import create_app

app = create_app()


def _find_available_port(start_port, host):
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]

if __name__ == "__main__":
    # Use debug mode only in development
    debug = os.getenv('FLASK_ENV') == 'development'
    host = os.getenv('HOST', '0.0.0.0')
    requested_port = int(os.getenv('PORT', 5000))
    port = _find_available_port(requested_port, host)
    if port != requested_port:
        print(f"Requested port {requested_port} was busy; using {port} instead.")
    app.run(host=host, port=port, debug=debug)

