# Security Policy

## Supported versions

Security fixes are applied to the latest release and `main`.

## Reporting a vulnerability

Please do not open a public issue for a vulnerability that enables command injection, arbitrary file overwrite outside user intent, unsafe path handling, or other security-sensitive behavior. Use GitHub's private vulnerability reporting if it is enabled for the repository.

## Media parsing risk

FFmpeg processes complex, attacker-controlled binary formats. Keep FFmpeg and your operating system patched. Avoid opening untrusted media with obsolete builds.

## Privacy boundary

Local Media Toolkit does not intentionally transmit media or telemetry. It invokes the locally installed `ffmpeg` and `ffprobe` executables. Your operating system, shell, FFmpeg distribution, codecs, endpoint security software, synced folders, and backup software remain outside this project's trust boundary.
