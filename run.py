import importlib.util
import os
import socket
import subprocess
import sys
import venv
from pathlib import Path

os.environ.setdefault('FLASK_ENV', 'development')

PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / '.venv'
REQUIREMENTS_FILE = PROJECT_ROOT / 'requirements.txt'
RUNTIME_IMPORTS = {
    'flask': 'Flask',
}


def _venv_python():
    if os.name == 'nt':
        return VENV_DIR / 'Scripts' / 'python.exe'
    return VENV_DIR / 'bin' / 'python'


def _missing_imports(python_executable=None):
    if python_executable is None:
        return [package for module, package in RUNTIME_IMPORTS.items() if importlib.util.find_spec(module) is None]

    check_script = (
        'import importlib.util, sys; '
        f'missing = [module for module in {list(RUNTIME_IMPORTS)!r} if importlib.util.find_spec(module) is None]; '
        'sys.exit(1 if missing else 0)'
    )
    result = subprocess.run([str(python_executable), '-c', check_script], check=False)
    return list(RUNTIME_IMPORTS.values()) if result.returncode else []


def _app_import_is_healthy(python_executable):
    health_script = (
        'from app import create_app; '
        'create_app()'
    )
    result = subprocess.run(
        [str(python_executable), '-c', health_script],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    return result.returncode == 0


def _install_requirements(python_executable, force=False):
    if not REQUIREMENTS_FILE.exists():
        raise FileNotFoundError(f'Cannot install dependencies because {REQUIREMENTS_FILE} does not exist.')

    command = [str(python_executable), '-m', 'pip', 'install']
    if force:
        command.extend(['--upgrade', '--force-reinstall'])
    command.extend(['-r', str(REQUIREMENTS_FILE)])
    subprocess.check_call(command)


def _ensure_local_runtime_environment():
    """Make `python run.py` work on a fresh checkout by using a healthy project virtualenv."""
    missing = _missing_imports()
    current_python = Path(sys.executable).resolve()
    current_is_healthy = not missing and _app_import_is_healthy(current_python)
    if current_is_healthy:
        return

    venv_python = _venv_python()
    if current_python == venv_python.resolve():
        target_python = current_python
    else:
        if not venv_python.exists():
            print('Creating local Python virtual environment in .venv ...')
            venv.EnvBuilder(with_pip=True).create(VENV_DIR)
        target_python = venv_python

    force_reinstall = not _app_import_is_healthy(target_python)
    print('Ensuring Python dependencies from requirements.txt are installed ...')
    _install_requirements(target_python, force=force_reinstall)

    if current_python != venv_python.resolve():
        reason = ', '.join(missing) if missing else 'an unhealthy runtime dependency set'
        print(f"Restarting with {venv_python} because the current Python is missing or failing: {reason}")
        os.execv(str(venv_python), [str(venv_python), *sys.argv])


if __name__ == "__main__":
    _ensure_local_runtime_environment()

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
