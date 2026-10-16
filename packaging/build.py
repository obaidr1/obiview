#!/usr/bin/python3
"""Create a small installable source/runtime bundle, without local user data."""
import hashlib
from pathlib import Path
import shutil
import tarfile
import tempfile

root = Path(__file__).resolve().parents[1]
output = root/'dist'/'Bildblick-0.9.2-linux.tar.gz'
output.parent.mkdir(exist_ok=True)
with tempfile.TemporaryDirectory(prefix='bildblick-package-') as staging:
    bundle = Path(staging)/'Bildblick-0.9.2'
    payload = bundle/'app'
    payload.mkdir(parents=True)
    for source in [*root.glob('*.py'), root/'start.sh', root/'README.txt',
                   root/'README.md', root/'PRODUCT.md', root/'LICENSE']:
        shutil.copy2(source, payload/source.name)
    shutil.copytree(root/'assets', payload/'assets')
    shutil.copytree(root/'docs', payload/'docs')
    shutil.copytree(root/'design-system', payload/'design-system', ignore=shutil.ignore_patterns('.*','__pycache__','node_modules'))
    for name in ('install.py', 'install.sh', 'INSTALLIEREN.txt'):
        shutil.copy2(root/'packaging'/name, bundle/name)
    shutil.copy2(root/'LICENSE', bundle/'LICENSE')
    (bundle/'install.sh').chmod(0o755)
    checksums = []
    for path in sorted(bundle.rglob('*')):
        if path.is_file():
            checksums.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(bundle)}')
    (bundle/'SHA256SUMS').write_text('\n'.join(checksums)+'\n', encoding='utf-8')
    with tarfile.open(output, 'w:gz') as archive:
        archive.add(bundle, arcname=bundle.name)
digest = hashlib.sha256(output.read_bytes()).hexdigest()
output.with_suffix(output.suffix+'.sha256').write_text(f'{digest}  {output.name}\n', encoding='utf-8')
print(output)
