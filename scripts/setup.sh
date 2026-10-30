#!/bin/bash
# Compatible with the Bash shipped by macOS.
set -eu
case "$(uname -s)" in Darwin) ;; *) echo 'Only macOS setup is supported.' >&2; exit 1 ;; esac
case "${1:-}" in ''|--check|--dry-run) ;; *) echo 'Usage: bash scripts/setup.sh [--check|--dry-run]' >&2; exit 2 ;; esac
if [ "$#" -gt 1 ]; then echo 'Expected at most one option.' >&2; exit 2; fi
if ! command -v brew >/dev/null; then echo 'Install Homebrew from https://brew.sh first.' >&2; exit 1; fi
if ! command -v python3 >/dev/null || ! python3 -c 'import sys; sys.exit(sys.version_info < (3,11))'; then
    case "${1:-}" in
        --check) echo 'Python >= 3.11 is required.' >&2; exit 1 ;;
        --dry-run) echo 'Would install Homebrew python, then prepare the local environment.'; exit 0 ;;
        *) brew install python ;;
    esac
fi
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
exec python3 "$script_dir/environment.py" "$@"
