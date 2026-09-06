from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def run(cmd):
    print("$", " ".join(map(str, cmd)))
    subprocess.run(cmd, check=True)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="localmedia-smoke-") as td:
        td = Path(td)
        src = td / "sample.mp4"
        out = td / "compressed.mp4"
        audio = td / "audio.mp3"
        run([
            "ffmpeg", "-y", "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24",
            "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100", "-t", "2",
            "-c:v", "libx264", "-c:a", "aac", str(src),
        ])
        run([sys.executable, "-m", "localmedia.cli", "compress", str(src), "-o", str(out), "--overwrite"])
        run([sys.executable, "-m", "localmedia.cli", "audio", str(src), "--to", "mp3", "-o", str(audio), "--overwrite"])
        assert out.exists() and out.stat().st_size > 0
        assert audio.exists() and audio.stat().st_size > 0
        print("Smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
