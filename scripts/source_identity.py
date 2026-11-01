"""Bind generated artifacts to their actual source bytes, independently of HEAD."""
import hashlib
from pathlib import Path


def fingerprint(root):
    root=Path(root)
    files=[]
    for folder in ('src','scripts'):
        files.extend(path for path in (root/folder).rglob('*')
                     if path.is_file() and (path.suffix in ('.py','.asm','.inc','.tcl','.sh') or path.name=='LICENSE'))
    files.extend(path for path in (root/'Makefile',root/'references/tools-lock.json') if path.exists())
    hashes={str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(files)}
    encoded=''.join(f'{name}\0{value}\n' for name,value in sorted(hashes.items())).encode()
    return dict(sha256=hashlib.sha256(encoded).hexdigest(),files=hashes)


def verify(root,expected):
    actual=fingerprint(root)
    if actual!=expected:
        raise ValueError('source identity differs from the qualified build; rebuild and requalify changed binaries')
