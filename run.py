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
<<<<<<< HEAD
    port_env = (os.getenv('PORT') or '').strip()
    port = 5000
    if port_env.isdigit():
        parsed_port = int(port_env)
        if 1 <= parsed_port <= 65535:
            port = parsed_port
=======
    requested_port = int(os.getenv('PORT', 5000))
    port = _find_available_port(requested_port, host)
    if port != requested_port:
        print(f"Requested port {requested_port} was busy; using {port} instead.")
>>>>>>> b15592d (Permanently fixing startup issues)
    app.run(host=host, port=port, debug=debug)

