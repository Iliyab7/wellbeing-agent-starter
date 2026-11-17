"""Container entrypoint: require explicit private bootstrap, then run API in foreground."""
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wellbeing.core import private_path


def main():
    home = private_path(os.environ.get('WELLBEING_MVP_HOME', '/state'))
    if not (home / 'memory.sqlite3').is_file() or not (home / 'credentials.private.json').is_file():
        raise SystemExit('Private runtime absent. Run the explicit bootstrap compose command first.')
    if not os.environ.get('WELLBEING_PUBLIC_URL'):
        raise SystemExit('Set approved stable HTTPS WELLBEING_PUBLIC_URL; terminate TLS at trusted proxy.')
    os.umask(0o077)
    from wellbeing.api import main as serve
    serve()


if __name__ == '__main__':
    main()
