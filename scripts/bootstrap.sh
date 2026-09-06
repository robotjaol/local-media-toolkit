#!/usr/bin/env bash
set -euo pipefail

echo "Local Media Toolkit bootstrap"

if ! command -v ffmpeg >/dev/null 2>&1; then
  case "$(uname -s)" in
    Darwin)
      if command -v brew >/dev/null 2>&1; then
        brew install ffmpeg
      else
        echo "Homebrew not found. Install FFmpeg using https://ffmpeg.org/download.html" >&2
        exit 1
      fi
      ;;
    Linux)
      if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update
        sudo apt-get install -y ffmpeg
      else
        echo "Unsupported Linux package manager. Install FFmpeg using your distribution packages." >&2
        exit 1
      fi
      ;;
    *)
      echo "Unsupported OS for bootstrap.sh" >&2
      exit 1
      ;;
  esac
fi

python3 -m venv .venv
. .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
localmedia doctor
