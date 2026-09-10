# Image converter tutorial

The desktop app has **Video** and **Image** tabs. Conversion runs on your computer;
you do not need to type commands or upload files. The Image tab processes a queue
of still images. Animated and multi-page inputs are rejected with a clear error,
rather than silently losing frames/pages. Video workflows remain available in the
Video tab and all existing CLI commands remain supported.

## Install and verify ImageMagick

Install Python 3.10+ with Tk, then install this project with `python -m pip install .`.
FFmpeg/FFprobe are required for Video only. ImageMagick is required for Image only.
Neither binary is bundled with the project.

### Windows 10 / 11

Use the installer linked from the [official ImageMagick download page](https://imagemagick.org/download/).
Enable its PATH option. Reopen your terminal and the app after installing:

```powershell
magick -version
magick identify -list format
```

The application uses ImageMagick 7's `magick` executable on Windows. It deliberately
does not use Windows' unrelated `convert.exe` disk utility. Use a Python installation
with Tcl/Tk support; `python -m tkinter` should open a test window.

### macOS

```bash
brew install imagemagick
magick -version
magick identify -list format
```

Use a Tk-enabled Python installation. Homebrew Python may need the matching
`python-tk` package for its Python version; verify with `python3 -m tkinter`.

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install imagemagick python3-tk python3-venv
```

For ImageMagick 7, run the `magick` checks above. Distribution packages that provide
ImageMagick 6 instead are supported on Linux/macOS using:

```bash
convert -version
identify -list format
```

The app verifies that the detected tool is ImageMagick before using it.

## Convert images in the GUI

1. Run `localmedia-gui` (or `python -m localmedia.gui`) and select **Image**.
2. Wait for format discovery. **Supported formats…** shows the installed coder list:
   `R` means readable input, `W` means writable output. **Refresh formats** repeats
   discovery. Restart the app if the system PATH changed.
3. Click **Add files…** and select one or more images. Repeat to add files from other
   folders. Input is identified from its contents, not just its extension.
4. Choose **Save folder**. The default is a `converted` folder alongside the first
   selected input. A missing folder is created when processing starts.
5. Choose **Format** from your installation's writable formats. Format listing is
   a capability report, not a guarantee: delegates, security policies and input
   content may still prevent an individual conversion.
6. Optionally set **Max width** and/or **Max height** in positive pixels. Images fit
   inside that bounding box, preserve aspect ratio and never upscale. Blank values
   keep the dimensions. Orientation metadata is applied before resizing.
7. **Quality** is enabled for the app's supported lossy-quality controls (JPEG,
   WebP, AVIF, HEIC/HEIF, JPEG 2000 and their listed aliases), only if that output
   coder is installed. Use 1–100, or leave blank for the encoder default. For other
   formats the field is disabled and no quality argument is sent. This value is
   encoder-specific and is not a target file size.
8. Click **Convert queue**. Each file shows Queued, Converting, Succeeded or Failed.
   The moving indicator means work is active; the file count is real and no
   percentage estimate is invented. The other tab remains usable.
9. Select a finished row and click **Open result** or **Open folder**. Select a failed
   row to read its full error. Fix the issue and click **Convert queue** again;
   successful rows are skipped and failed rows are retried.

Outputs use `original-name_converted.ext`. Existing names get a numeric suffix,
such as `original-name_converted_2.ext`. Original files and existing outputs are
never overwritten. Inputs from different directories with the same name receive
distinct outputs. The image backend stages its work in a temporary directory and
copies a completed result using exclusive file creation, including a final collision
check. Temporary copies are removed after success or failure. Allow disk space for
the source copy, encoded result and final output.

## Equivalent ImageMagick commands

Assuming your installation reports JPEG write support, GUI settings JPEG, quality
85 and a 1600 × 1200 bounding box correspond to:

```bash
magick "holiday photo.png" -auto-orient -resize "1600x1200>" -quality 85 "JPEG:holiday photo_converted.jpeg"
```

For PNG without resizing or a quality override:

```bash
magick "holiday photo.jpg" -auto-orient "PNG:holiday photo_converted.png"
```

With ImageMagick 6 use `convert` instead of `magick`. These examples explain the
transformation; the GUI additionally validates files and protects existing outputs.
Direct ImageMagick commands can replace an existing destination: choose a new name.
The GUI passes separate subprocess arguments without a shell and stages input under
a literal filename, including for names containing spaces, brackets or percent signs.

## Troubleshooting

| Problem | Next step |
|---|---|
| ImageMagick not found | Verify the commands above, install/add it to PATH, then restart the app. Video still works independently. |
| No writable formats | Check the ImageMagick installation and the output of `identify -list format`. |
| Desired format missing | Your build does not advertise that encoder. Install an appropriate ImageMagick build/delegate and refresh. |
| Invalid image / no decode delegate | Open the original in an image viewer, check that it is not corrupt, and verify its read coder/delegate. Renaming the extension does not convert a file. |
| Security policy error | Review the detailed error and the installation's policy. Use an allowed format; do not disable all protections. |
| Animation / multiple pages | Export one still frame/page first. This GUI currently handles single-image inputs. |
| Permission denied / disk full | Choose a writable folder and free enough disk space for temporary and final files, then retry. |
| Coder did not produce a single file | Choose a file-based image format; some reported coders represent devices or special output modes. |
| Cannot open result | Verify the file still exists and that the OS has an associated viewer; use Open folder. |
| Missing tkinter | Install Tk for the same Python interpreter used to launch the app. |

See the official [format reference](https://imagemagick.org/formats/),
[command options](https://imagemagick.org/command-line-options/), and
[installation guidance](https://imagemagick.org/download/) for coder/delegate details.
