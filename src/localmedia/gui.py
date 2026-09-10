from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .images import ImageTools, convert_image, discover_imagemagick, supports_quality


def available_output(source: Path, folder: Path, extension: str) -> Path:
    output = folder / f"{source.stem}_converted.{extension.lower()}"
    number = 2
    while output.exists():
        output = folder / f"{source.stem}_converted_{number}.{extension.lower()}"
        number += 1
    return output


def video_command(source: Path, output: Path, action: str, fmt: str, crf: int) -> list[str]:
    command = [sys.executable, "-m", "localmedia.cli", action, str(source), "-o", str(output)]
    if action == "convert":
        command += ["--to", fmt]
    elif action == "compress":
        command += ["--crf", str(crf)]
    return command


class ConverterTab(ttk.Frame):
    def __init__(self, parent: ttk.Notebook, media: str) -> None:
        super().__init__(parent, padding=16)
        self.media = media
        self.events: queue.Queue = queue.Queue()
        self.busy = False
        self.tools: ImageTools | None = None
        self.sources: dict[str, Path] = {}
        self.results: dict[str, Path] = {}
        self.details: dict[str, str] = {}
        self.controls: list[ttk.Widget] = []
        self.folder = tk.StringVar()
        self.format = tk.StringVar(value="mp4" if media == "Video" else "")
        self.action = tk.StringVar(value="compress")
        self.quality = tk.StringVar(value="85")
        self.crf = tk.StringVar(value="28")
        self.width = tk.StringVar()
        self.height = tk.StringVar()
        self.status = tk.StringVar(value="Add files to start. Originals are always preserved.")
        self.backend = tk.StringVar(value="FFmpeg runs locally. No upload required.")
        self._build()
        self.after(100, self._poll)
        if media == "Image":
            self.refresh_formats()

    def button(self, parent: ttk.Frame, text: str, command) -> ttk.Button:
        button = ttk.Button(parent, text=text, command=command)
        self.controls.append(button)
        return button

    def entry(self, parent: ttk.Frame, variable: tk.StringVar, width: int = 12) -> ttk.Entry:
        entry = ttk.Entry(parent, textvariable=variable, width=width)
        self.controls.append(entry)
        return entry

    def _build(self) -> None:
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        toolbar = ttk.Frame(self)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        ttk.Label(toolbar, text="1  Select files", style="Section.TLabel").pack(side="left")
        self.button(toolbar, "Add files…", self.add_files).pack(side="right")
        self.button(toolbar, "Remove selected", self.remove_files).pack(side="right", padx=8)
        ttk.Label(self, textvariable=self.backend, wraplength=680).grid(
            row=1, column=0, sticky="w", pady=(0, 8)
        )
        table = ttk.Frame(self)
        table.grid(row=2, column=0, sticky="nsew")
        table.columnconfigure(0, weight=1)
        table.rowconfigure(0, weight=1)
        self.tree = ttk.Treeview(table, columns=("file", "status", "output"), show="headings")
        for name, label, width in (
            ("file", "Input file", 250), ("status", "Status", 100), ("output", "Result", 260)
        ):
            self.tree.heading(name, text=label)
            self.tree.column(name, width=width, minwidth=80)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.tree.yview)
        scroll.grid(row=0, column=1, sticky="ns")
        horizontal = ttk.Scrollbar(table, orient="horizontal", command=self.tree.xview)
        horizontal.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        self.tree.bind("<<TreeviewSelect>>", self.show_detail)
        settings = ttk.Frame(self)
        settings.grid(row=3, column=0, sticky="ew", pady=12)
        settings.columnconfigure(1, weight=1)
        ttk.Label(settings, text="2  Set output", style="Section.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8)
        )
        ttk.Label(settings, text="Save folder").grid(row=1, column=0, sticky="w", padx=(0, 12))
        self.entry(settings, self.folder).grid(row=1, column=1, sticky="ew")
        self.button(settings, "Browse…", self.pick_folder).grid(row=1, column=2, padx=(8, 0))
        options = ttk.Frame(settings)
        options.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(10, 0))
        ttk.Label(options, text="Format").grid(row=0, column=0, sticky="w")
        self.format_box = ttk.Combobox(
            options, textvariable=self.format, state="readonly", width=12,
            values=["mp4", "mov", "mkv", "webm", "avi"] if self.media == "Video" else [],
        )
        self.format_box.grid(row=1, column=0, sticky="w", padx=(0, 16))
        self.controls.append(self.format_box)
        self.format_box.bind("<<ComboboxSelected>>", lambda event: self.update_options())
        if self.media == "Video":
            ttk.Label(options, text="Action").grid(row=0, column=1, sticky="w")
            action_box = ttk.Combobox(
                options, textvariable=self.action, state="readonly", width=18,
                values=["compress", "convert", "strip-metadata"],
            )
            action_box.grid(row=1, column=1, padx=(0, 16))
            action_box.bind("<<ComboboxSelected>>", lambda event: self.update_options())
            self.controls.append(action_box)
            ttk.Label(options, text="CRF (0–51)").grid(row=0, column=2, sticky="w")
            self.crf_entry = self.entry(options, self.crf, 8)
            self.crf_entry.grid(row=1, column=2)
            hint = (
                "Compress: H.264 MP4. Lower CRF = higher quality. Strip metadata keeps the format."
            )
        else:
            for column, label, variable in (
                (1, "Quality (1–100)", self.quality),
                (2, "Max width (px)", self.width), (3, "Max height (px)", self.height),
            ):
                ttk.Label(options, text=label).grid(row=0, column=column, sticky="w")
                entry = self.entry(options, variable, 12)
                entry.grid(row=1, column=column, padx=(0, 12))
                if column == 1:
                    self.quality_entry = entry
            self.button(settings, "Refresh formats", self.refresh_formats).grid(
                row=3, column=0, sticky="w", pady=(8, 0)
            )
            self.button(settings, "Supported formats…", self.show_formats).grid(
                row=3, column=1, sticky="w", pady=(8, 0)
            )
            hint = "Still images only. Blank size keeps dimensions; resize fits without upscaling."
        ttk.Label(settings, text=hint, wraplength=680).grid(
            row=4, column=0, columnspan=3, sticky="w", pady=(8, 0)
        )
        actions = ttk.Frame(self)
        actions.grid(row=4, column=0, sticky="ew")
        self.run_button = self.button(actions, "3  Convert queue", self.run_jobs)
        self.run_button.pack(side="left")
        ttk.Button(actions, text="Open result", command=self.open_result).pack(side="left", padx=8)
        ttk.Button(actions, text="Open folder", command=self.open_folder).pack(side="left")
        self.progress = ttk.Progressbar(actions, mode="indeterminate", length=100)
        self.progress.pack(side="right")
        ttk.Label(self, textvariable=self.status, wraplength=680).grid(
            row=5, column=0, sticky="w", pady=8
        )
        self.detail = tk.Text(self, height=4, wrap="word", state="disabled", font="TkDefaultFont")
        self.detail.grid(row=6, column=0, sticky="ew")
        self.update_options()

    def update_options(self) -> None:
        if self.busy:
            return
        if self.media == "Image":
            self.quality_entry.configure(
                state="normal" if supports_quality(self.format.get()) else "disabled"
            )
            self.run_button.configure(state="normal" if self.tools else "disabled")
        else:
            self.crf_entry.configure(
                state="normal" if self.action.get() == "compress" else "disabled"
            )
            self.format_box.configure(
                state="readonly" if self.action.get() == "convert" else "disabled"
            )

    def set_busy(self, busy: bool) -> None:
        self.busy = busy
        for control in self.controls:
            control.configure(state="disabled" if busy else (
                "readonly" if isinstance(control, ttk.Combobox) else "normal"
            ))
        if busy:
            self.progress.start(15)
        else:
            self.progress.stop()
            self.update_options()

    def refresh_formats(self) -> None:
        self.set_busy(True)
        self.backend.set("Checking installed ImageMagick formats…")
        threading.Thread(target=self._discover, daemon=True).start()

    def _discover(self) -> None:
        try:
            self.events.put(("tools", discover_imagemagick()))
        except Exception as exc:
            self.events.put(("tools_error", str(exc)))

    def show_formats(self) -> None:
        if not self.tools:
            return
        window = tk.Toplevel(self)
        window.title("Installed ImageMagick formats")
        text = tk.Text(window, width=85, height=24, wrap="word")
        text.pack(fill="both", expand=True)
        text.insert(
            "end", "R = input, W = output. Delegates/policy may restrict individual files.\n\n"
        )
        for fmt in sorted(self.tools.formats.values(), key=lambda item: item.name):
            text.insert("end", f"{fmt.name}: {'R' if fmt.readable else '-'}"
                        f"{'W' if fmt.writable else '-'}  {fmt.description}\n")
        text.configure(state="disabled")

    def add_files(self) -> None:
        paths = filedialog.askopenfilenames(parent=self, title=f"Select {self.media.lower()} files")
        for name in paths:
            path = Path(name).resolve()
            if path not in self.sources.values():
                item = self.tree.insert("", "end", values=(path.name, "Queued", "—"))
                self.sources[item] = path
                self.details[item] = str(path)
        if paths and not self.folder.get():
            self.folder.set(str(Path(paths[0]).parent / "converted"))
        self.status.set(f"{len(self.sources)} files in queue. Select a row to view details.")

    def remove_files(self) -> None:
        for item in self.tree.selection():
            self.tree.delete(item)
            self.sources.pop(item, None)
            self.results.pop(item, None)
            self.details.pop(item, None)
        self.status.set(f"{len(self.sources)} files in queue.")

    def pick_folder(self) -> None:
        path = filedialog.askdirectory(parent=self, title="Choose output folder")
        if path:
            self.folder.set(path)

    def show_detail(self, event=None) -> None:
        selected = self.tree.selection()
        content = self.details.get(selected[0], "") if selected else ""
        self.detail.configure(state="normal")
        self.detail.delete("1.0", "end")
        self.detail.insert("end", content)
        self.detail.configure(state="disabled")

    def open_path(self, path: Path) -> None:
        try:
            if not path.exists():
                raise OSError(f"Path no longer exists: {path}")
            if sys.platform == "win32":
                os.startfile(str(path))
            else:
                subprocess.Popen(["open" if sys.platform == "darwin" else "xdg-open", str(path)])
        except OSError as exc:
            messagebox.showerror("Cannot open result", str(exc), parent=self)

    def open_result(self) -> None:
        selected = self.tree.selection()
        if selected and selected[0] in self.results:
            self.open_path(self.results[selected[0]])
        else:
            self.status.set("Select a successfully converted file to open its result.")

    def open_folder(self) -> None:
        selected = self.tree.selection()
        if selected and selected[0] in self.results:
            self.open_path(self.results[selected[0]].parent)
        elif self.folder.get().strip():
            self.open_path(Path(self.folder.get()).expanduser().resolve())
        else:
            self.status.set("Choose an output folder first.")

    def run_jobs(self) -> None:
        if self.busy:
            return
        jobs = [(item, source) for item, source in self.sources.items() if item not in self.results]
        try:
            if not jobs:
                raise ValueError("Add files, or remove completed files and add them again.")
            if not self.folder.get().strip():
                raise ValueError("Choose an output folder.")
            folder = Path(self.folder.get()).expanduser().resolve()
            options = {}
            crf = 28
            if self.media == "Image":
                if not self.tools or self.format.get() not in self.tools.formats:
                    raise ValueError("Refresh formats and select an available output format.")
                for name, variable in (("width", self.width), ("height", self.height)):
                    options[name] = int(variable.get()) if variable.get().strip() else None
                    if options[name] is not None and options[name] <= 0:
                        raise ValueError("Dimensions must be positive whole numbers.")
                if supports_quality(self.format.get()) and self.quality.get().strip():
                    options["quality"] = int(self.quality.get())
                    if not 1 <= options["quality"] <= 100:
                        raise ValueError("Quality must be between 1 and 100.")
            elif self.action.get() == "compress":
                crf = int(self.crf.get())
                if not 0 <= crf <= 51:
                    raise ValueError("CRF must be between 0 and 51.")
        except ValueError as exc:
            messagebox.showerror("Check output settings", str(exc), parent=self)
            return
        for item, source in jobs:
            self.tree.item(item, values=(source.name, "Queued", "—"))
        self.set_busy(True)
        self.status.set(f"Converting {len(jobs)} files locally…")
        threading.Thread(
            target=self._worker,
            args=(jobs, folder, self.format.get(), self.action.get(), crf, options, self.tools),
            daemon=True,
        ).start()

    def _worker(self, jobs, folder, fmt, action, crf, options, tools) -> None:
        succeeded = 0
        for index, (item, source) in enumerate(jobs, 1):
            self.events.put(("running", item, f"Processing file {index} of {len(jobs)}…"))
            try:
                folder.mkdir(parents=True, exist_ok=True)
                extension = fmt
                if self.media == "Video":
                    extension = "mp4" if action == "compress" else (
                        source.suffix.lstrip(".") if action == "strip-metadata" else fmt
                    )
                output = available_output(source, folder, extension)
                if self.media == "Image":
                    convert_image(tools, source, output, fmt, **options)
                else:
                    result = subprocess.run(
                        video_command(source, output, action, fmt, crf),
                        capture_output=True, text=True, errors="replace", check=False,
                        stdin=subprocess.DEVNULL,
                    )
                    if result.returncode:
                        raise RuntimeError(
                            "Check FFmpeg installation, input format and folder permissions.\n"
                            + result.stderr.strip() + "\n" + result.stdout.strip()
                        )
                    if not output.is_file() or not output.stat().st_size:
                        raise RuntimeError("FFmpeg did not produce an output file.")
                succeeded += 1
                self.events.put(("success", item, output))
            except Exception as exc:
                self.events.put((
                    "failure", item, f"{source}\n{exc}\nFix the issue and retry the queue."
                ))
        self.events.put(("done", succeeded, len(jobs) - succeeded))

    def _poll(self) -> None:
        # Only the Tk thread changes widgets; workers communicate through this queue.
        try:
            while True:
                kind, *data = self.events.get_nowait()
                if kind == "tools":
                    self.tools = data[0]
                    writable = sorted(f.name for f in self.tools.formats.values() if f.writable)
                    self.format_box.configure(values=writable)
                    if self.format.get() not in writable:
                        self.format.set("PNG" if "PNG" in writable else writable[0])
                    self.backend.set(
                        f"ImageMagick ready · {len(writable)} writable formats. "
                        "Availability depends on installed delegates and policy."
                    )
                    self.set_busy(False)
                elif kind == "tools_error":
                    self.tools = None
                    self.format_box.configure(values=[])
                    self.format.set("")
                    self.backend.set(data[0])
                    self.set_busy(False)
                elif kind == "running":
                    self.tree.set(data[0], "status", "Converting…")
                    self.status.set(data[1])
                elif kind == "success":
                    item, output = data
                    self.results[item] = output
                    self.details[item] = f"Input: {self.sources[item]}\nSaved: {output}"
                    self.tree.item(item, values=(self.sources[item].name, "Succeeded", str(output)))
                    self.show_detail()
                elif kind == "failure":
                    item, detail = data
                    self.details[item] = detail
                    self.tree.item(
                        item, values=(self.sources[item].name, "Failed", "Select for details")
                    )
                    self.tree.selection_set(item)
                    self.show_detail()
                elif kind == "done":
                    self.set_busy(False)
                    self.status.set(
                        f"Finished: {data[0]} succeeded, {data[1]} failed. "
                        "Open a result or retry failed files with Convert queue."
                    )
        except queue.Empty:
            pass
        self.after(100, self._poll)


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Local Media Toolkit")
        self.geometry("1000x780")
        self.minsize(760, 700)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", font="TkDefaultFont", background="#f4f6f9", foreground="#172337")
        style.configure("TButton", padding=(12, 7))
        style.configure("TNotebook.Tab", padding=(24, 10))
        style.configure("Treeview", rowheight=30, background="#ffffff", fieldbackground="#ffffff")
        style.map(
            "Treeview", background=[("selected", "#225bc4")], foreground=[("selected", "white")]
        )
        style.configure("Section.TLabel", font=("TkDefaultFont", 11, "bold"))
        header = ttk.Frame(self, padding=(20, 16))
        header.pack(fill="x")
        ttk.Label(
            header, text="Local Media Toolkit", font=("TkDefaultFont", 21, "bold")
        ).pack(anchor="w")
        ttk.Label(
            header, text="Convert video and images in one app. Local files, no manual commands.",
        ).pack(anchor="w", pady=(5, 0))
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=20, pady=(0, 16))
        self.tabs = [ConverterTab(notebook, media) for media in ("Video", "Image")]
        for tab in self.tabs:
            notebook.add(tab, text=tab.media)
        self.protocol("WM_DELETE_WINDOW", self.close)

    def close(self) -> None:
        if any(tab.busy for tab in self.tabs):
            messagebox.showinfo(
                "Processing in progress", "Wait for the current queue to finish before closing.",
                parent=self,
            )
            return
        self.destroy()


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
