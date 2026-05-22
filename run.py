from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    # Use debug mode only in development
    debug = os.getenv('FLASK_ENV') == 'development'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))
    app.run(host=host, port=port, debug=debug)

