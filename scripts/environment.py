#!/usr/bin/env python3
"""Prepare local pinned tools, preserving existing environments and inputs."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / 'references/tools-lock.json').read_text())
SJASM = ROOT / '.tools/sjasmplus/sjasmplus'
COMMIT = 'd379eeac9ad3857fb48fd3a3929175d0a56038ce'


def run(args, **kwargs):
    return subprocess.run([str(x) for x in args], cwd=ROOT, check=True,
                          env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'}, **kwargs)


def output(args):
    return run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True).stdout.strip()


def validate_checkout(path, commit):
    if output(['git', '-C', path, 'rev-parse', 'HEAD']) != commit:
        raise ValueError(f'{path}: unexpected revision; existing tools were not reset')
    run(['git', '-C', path, 'diff', '--quiet', 'HEAD'])


def prepare_checkout(path, repository, commit, tag=None):
    if not path.exists():
        args = ['git', 'clone']
        if tag:
            args += ['--depth', '1', '--branch', tag]
        run(args + [repository, path])
        if not tag:
            run(['git', '-C', path, 'checkout', '--detach', commit])
    validate_checkout(path, commit)


def mads_digest():
    key = {'arm64': 'macos_aarch64_sha256', 'x86_64': 'macos_x86_64_sha256'}[platform.machine()]
    return LOCK['mads'][key]


def check():
    problems = []
    for tool in ('git', 'cc', 'make', 'brew', 'openmsx', 'stella', 'dasm'):
        if not shutil.which(tool):
            problems.append(f'missing {tool}')
    python = ROOT / '.venv/bin/python'
    if not python.exists():
        problems.append('missing .venv/bin/python')
    else:
        try:
            run([python, '-c', 'import sys; assert sys.version_info >= (3,11)'], stdout=subprocess.DEVNULL)
            run([python, '-m', 'pip', 'check'], stdout=subprocess.DEVNULL)
        except subprocess.CalledProcessError:
            problems.append('existing .venv is incompatible; preserve it and repair explicitly')
    try:
        validate_checkout(SJASM.parent, COMMIT)
        if output([SJASM, '--nologo', '--version']) != '1.24.0':
            problems.append('unexpected sjasmplus version')
    except (OSError, ValueError, subprocess.CalledProcessError):
        problems.append('missing or unverified pinned sjasmplus')
    try:
        path = ROOT / '.tools/distella'
        validate_checkout(path, LOCK['distella']['commit'])
        digest = hashlib.sha256((path / 'source/distella.c').read_bytes()).hexdigest()
        if digest != LOCK['distella']['source_sha256'] or not os.access(path / 'distella', os.X_OK):
            problems.append('missing or unverified DiStella')
    except (OSError, ValueError, subprocess.CalledProcessError):
        problems.append('missing or unverified pinned DiStella')
    mads = ROOT / '.tools/mads'
    if not mads.exists() or hashlib.sha256(mads.read_bytes()).hexdigest() != mads_digest() or not os.access(mads, os.X_OK):
        problems.append('missing or unverified pinned MADS')
    return problems


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    if platform.system() != 'Darwin' or platform.machine() not in ('arm64', 'x86_64'):
        parser.error('supported hosts: macOS arm64/x86_64')
    if args.check and args.dry_run:
        parser.error('choose --check or --dry-run')
    if args.dry_run:
        print('Would check Homebrew and command-line build tools; install missing openmsx/stella/dasm;')
        print('preserve/create .venv; prepare pinned local sjasmplus/DiStella/MADS; verify versions/hashes.')
        print('No changes applied. Intel support is prepared but has not been exercised here.')
        return 0
    try:
        if not args.check:
            for tool in ('git', 'cc', 'make', 'brew'):
                if not shutil.which(tool):
                    raise ValueError(f'missing {tool}; install Xcode command-line tools/Homebrew first')
            for formula in ('openmsx', 'stella', 'dasm'):
                if not shutil.which(formula):
                    run(['brew', 'install', formula])
            venv = ROOT / '.venv'
            if not venv.exists():
                run([sys.executable, '-m', 'venv', venv])
                run([venv / 'bin/python', '-m', 'pip', 'install', '--upgrade', 'pip', 'setuptools', 'wheel'])
            (ROOT / '.tools').mkdir(exist_ok=True)
            prepare_checkout(SJASM.parent, 'https://github.com/z00m128/sjasmplus.git', COMMIT, 'v1.24.0')
            if not SJASM.exists():
                run(['make', '-C', SJASM.parent, '-j2', 'USE_LUA=0'])
            distella = ROOT / '.tools/distella'
            prepare_checkout(distella, LOCK['distella']['repository'], LOCK['distella']['commit'])
            if not (distella / 'distella').exists():
                run(['make', '-C', distella, 'auto'])
            mads = ROOT / '.tools/mads'
            if not mads.exists():
                arch = 'macos_aarch64' if platform.machine() == 'arm64' else 'macos_x86_64'
                url = f"https://raw.githubusercontent.com/tebe6502/Mad-Assembler/{LOCK['mads']['commit']}/bin/{arch}/mads"
                data = urllib.request.urlopen(url, timeout=60).read()
                if hashlib.sha256(data).hexdigest() != mads_digest():
                    raise ValueError('MADS download checksum mismatch')
                mads.write_bytes(data)
                mads.chmod(0o755)
        problems = check()
        if problems:
            print('\n'.join(problems), file=sys.stderr)
            return 1
        print('Environment verified: local Python, pinned assemblers, openMSX, Stella and DASM.')
        return 0
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f'Environment preparation failed: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
