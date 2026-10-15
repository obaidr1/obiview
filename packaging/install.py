#!/usr/bin/python3
"""Install Bildblick for the current user, without root or package downloads."""
import argparse
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile

APP_ID = 'local.bildblick.Viewer'


def atomic_text(path, content, mode=0o644):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.bildblick-install-', dir=path.parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            stream.write(content)
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def exec_argument(value):
    # Escape Exec quoting, then Desktop Entry string escaping.
    value = str(value).replace('%', '%%')
    for char in ('\\', '"', '`', '$'):
        value = value.replace(char, '\\' + char)
    return '"' + value.replace('\\', '\\\\') + '"'


def install(source, data_dir, bin_dir):
    source = source.resolve()
    if not (source/'bildblick.py').is_file():
        raise ValueError(f'Anwendungsdateien fehlen: {source}')
    subprocess.run(['/usr/bin/python3', '-c',
        "import gi, cairo, PIL; gi.require_version('Gtk','4.0'); "
        "gi.require_version('GdkPixbuf','2.0'); from gi.repository import Gtk, GdkPixbuf; "
        "assert int(PIL.__version__.split('.')[0]) >= 12, 'Pillow 12 oder neuer erforderlich'"], check=True)
    app_dir = data_dir/'bildblick'/'app'
    app_dir.mkdir(parents=True, exist_ok=True)
    for original in [*source.glob('*.py'), source/'start.sh', source/'README.txt',
                     source/'README.md', source/'PRODUCT.md', source/'LICENSE']:
        target = app_dir/original.name
        if original.resolve() != target.resolve():
            shutil.copy2(original, target)
    if (source/'docs').is_dir():
        shutil.copytree(source/'docs',app_dir/'docs',dirs_exist_ok=True)
    (app_dir/'start.sh').chmod(0o755)
    launcher = bin_dir/'bildblick'
    atomic_text(launcher, '#!/bin/sh\nexec /usr/bin/python3 ' + shlex.quote(str(app_dir/'bildblick.py')) + ' "$@"\n', 0o755)
    icon = data_dir/'icons'/'hicolor'/'scalable'/'apps'/(APP_ID+'.svg')
    icon.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source/'assets'/(APP_ID+'.svg'), icon)
    desktop = data_dir/'applications'/(APP_ID+'.desktop')
    atomic_text(desktop, f'''[Desktop Entry]
Version=1.0
Type=Application
Name=Bildblick
GenericName=Bildbetrachter
Comment=Bilder anzeigen, bearbeiten und konvertieren
Exec={exec_argument(launcher)} %f
Icon={APP_ID}
Terminal=false
Categories=Graphics;Viewer;Photography;
Keywords=Bilder;Fotos;Image;Photo;Resize;
MimeType=image/png;image/jpeg;image/webp;image/bmp;image/tiff;image/gif;image/svg+xml;image/avif;image/x-icon;image/jp2;application/pdf;
StartupNotify=true
StartupWMClass={APP_ID}
''')
    # Replace only the starter created by earlier Bildblick development versions.
    legacy = data_dir/'applications'/'bildblick.desktop'
    if legacy.exists():
        old = legacy.read_text(encoding='utf-8')
        if 'Name=Bildblick\n' in old and '/start.sh %f' in old:
            legacy.unlink()
    if shutil.which('desktop-file-validate'):
        subprocess.run(['desktop-file-validate', str(desktop)], check=True)
    if shutil.which('update-desktop-database'):
        subprocess.run(['update-desktop-database', str(desktop.parent)], check=True)
    if shutil.which('gtk-update-icon-cache'):
        subprocess.run(['gtk-update-icon-cache', '-f', '-t', str(data_dir/'icons'/'hicolor')], check=True)
    print(f'Bildblick ist installiert. Im Anwendungsmenü nach „Bildblick“ suchen.\n'
          f'Starter: {desktop}\nProgramm: {app_dir}\nTerminal: {launcher}')
    return app_dir, desktop


def main():
    parser = argparse.ArgumentParser(description='Bildblick im eigenen Benutzerkonto installieren')
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent/'app')
    parser.add_argument('--data-dir', type=Path, default=Path(os.environ.get('XDG_DATA_HOME') or Path.home()/'.local/share'))
    parser.add_argument('--bin-dir', type=Path, default=Path.home()/'.local/bin')
    args = parser.parse_args()
    try:
        install(args.source, args.data_dir.expanduser().absolute(), args.bin_dir.expanduser().absolute())
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Installation fehlgeschlagen: {error}\n'
                    'Benötigt: Python 3, GTK 4, PyGObject, Pycairo und Pillow ab Version 12.\n')


if __name__ == '__main__':
    main()
