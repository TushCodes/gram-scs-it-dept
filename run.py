from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    # Use debug mode only in development
    debug = os.getenv('FLASK_ENV') == 'development'
    host = os.getenv('HOST', '0.0.0.0')
    port_env = (os.getenv('PORT') or '').strip()
    port = 5000
    if port_env.isdigit():
        parsed_port = int(port_env)
        if 1 <= parsed_port <= 65535:
            port = parsed_port
    app.run(host=host, port=port, debug=debug)

