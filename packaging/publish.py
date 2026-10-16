#!/usr/bin/python3
"""Publish the reviewed main branch and versioned package through GitHub CLI."""
import argparse
import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = 'obaidr1/obiview'
VERSION = '0.6.0'


def run(*args, capture=False, check=True):
    return subprocess.run(args, cwd=ROOT, check=check, text=True,
                          capture_output=capture)


def publish():
    run('gh', 'api', 'user', '--jq', '.login', capture=True)
    if run('git', 'branch', '--show-current', capture=True).stdout.strip() != 'main':
        raise ValueError('Bitte den geprüften main-Branch auswählen.')
    if run('git', 'status', '--porcelain', capture=True).stdout.strip():
        raise ValueError('Bitte alle vorgesehenen Änderungen vor der Veröffentlichung committen.')
    run('/usr/bin/python3', '-m', 'unittest', 'discover', '-s', 'tests', '-v')
    run('/usr/bin/python3', 'packaging/build.py')
    existing = run('gh', 'repo', 'view', REPOSITORY, '--json', 'nameWithOwner,isPrivate', capture=True, check=False)
    if existing.returncode == 0:
        if json.loads(existing.stdout)['isPrivate']:
            raise ValueError('Das Zielrepository ist privat. Sichtbarkeit bitte vor der Veröffentlichung prüfen.')
    else:
        run('gh', 'repo', 'create', REPOSITORY, '--public', '--description',
            'Native Linux image viewer and editor with precise export options, batch processing and a CLI.')
    expected = f'https://github.com/{REPOSITORY}.git'
    origin = run('git', 'remote', 'get-url', 'origin', capture=True, check=False)
    if origin.returncode:
        run('git', 'remote', 'add', 'origin', expected)
    elif origin.stdout.strip() not in (expected, f'git@github.com:{REPOSITORY}.git'):
        raise ValueError('origin zeigt auf ein anderes Repository; kein automatisches Überschreiben.')
    run('git', 'push', '-u', 'origin', 'main')
    tag = 'v'+VERSION
    head = run('git', 'rev-parse', 'HEAD', capture=True).stdout.strip()
    existing_tag = run('git', 'rev-parse', '--verify', tag+'^{commit}', capture=True, check=False)
    if existing_tag.returncode:
        run('git', 'tag', '-a', tag, '-m', 'Bildblick '+VERSION)
    elif existing_tag.stdout.strip() != head:
        raise ValueError('Der Versionstag zeigt auf einen anderen Commit; Version erhöhen statt überschreiben.')
    run('git', 'push', 'origin', tag)
    release = run('gh', 'release', 'view', tag, '--repo', REPOSITORY, capture=True, check=False)
    if release.returncode == 0:
        print('Release existiert bereits; bestehende Release-Dateien bleiben unverändert.')
    else:
        package = ROOT/'dist'/f'Bildblick-{VERSION}-linux.tar.gz'
        run('gh', 'release', 'create', tag, str(package), str(package)+'.sha256',
            '--repo', REPOSITORY, '--verify-tag', '--prerelease', '--title', 'Bildblick '+VERSION,
            '--notes-file', str(ROOT/'docs'/f'release-{VERSION}.md'))
    print(f'https://github.com/{REPOSITORY}')
    print(f'https://github.com/{REPOSITORY}/releases/tag/{tag}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Bildblick-Code und Vorabversion auf GitHub veröffentlichen')
    parser.parse_args()
    try:
        publish()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'Veröffentlichung nicht abgeschlossen: {error}\n')
