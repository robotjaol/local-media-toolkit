from __future__ import annotations

import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Local Media Toolkit")
        self.geometry("720x460")
        self.minsize(640, 420)

        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.action_var = tk.StringVar(value="compress")
        self.format_var = tk.StringVar(value="mp4")
        self.crf_var = tk.StringVar(value="28")
        self.status_var = tk.StringVar(value="Ready. Processing stays on this computer.")

        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self, padding=18)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Local Media Toolkit", font=("TkDefaultFont", 18, "bold")).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 4)
        )
        ttk.Label(frame, text="No upload. No cloud converter. FFmpeg runs locally.").grid(
            row=1, column=0, columnspan=3, sticky="w", pady=(0, 18)
        )

        ttk.Label(frame, text="Input").grid(row=2, column=0, sticky="w")
        ttk.Entry(frame, textvariable=self.input_var).grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Browse", command=self.pick_input).grid(row=3, column=2, sticky="ew")

        ttk.Label(frame, text="Output").grid(row=4, column=0, sticky="w", pady=(14, 0))
        ttk.Entry(frame, textvariable=self.output_var).grid(row=5, column=0, columnspan=2, sticky="ew", padx=(0, 8))
        ttk.Button(frame, text="Save as", command=self.pick_output).grid(row=5, column=2, sticky="ew")

        ttk.Label(frame, text="Action").grid(row=6, column=0, sticky="w", pady=(14, 0))
        actions = ttk.Combobox(
            frame,
            textvariable=self.action_var,
            values=["compress", "convert", "strip-metadata"],
            state="readonly",
        )
        actions.grid(row=7, column=0, sticky="ew", padx=(0, 8))

        ttk.Label(frame, text="Format").grid(row=6, column=1, sticky="w", pady=(14, 0))
        ttk.Combobox(
            frame,
            textvariable=self.format_var,
            values=["mp4", "mov", "mkv", "webm", "avi"],
            state="readonly",
        ).grid(row=7, column=1, sticky="ew", padx=(0, 8))

        ttk.Label(frame, text="CRF (compress)").grid(row=6, column=2, sticky="w", pady=(14, 0))
        ttk.Entry(frame, textvariable=self.crf_var, width=8).grid(row=7, column=2, sticky="ew")

        ttk.Separator(frame).grid(row=8, column=0, columnspan=3, sticky="ew", pady=20)
        ttk.Button(frame, text="Run locally", command=self.run_job).grid(row=9, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.status_var, wraplength=650).grid(
            row=10, column=0, columnspan=3, sticky="w", pady=(16, 0)
        )

        self.log = tk.Text(frame, height=9, wrap="word", state="disabled")
        self.log.grid(row=11, column=0, columnspan=3, sticky="nsew", pady=(12, 0))

        frame.columnconfigure(0, weight=2)
        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(2, weight=1)
        frame.rowconfigure(11, weight=1)

    def pick_input(self) -> None:
        path = filedialog.askopenfilename(title="Select media file")
        if path:
            self.input_var.set(path)
            src = Path(path)
            if not self.output_var.get():
                self.output_var.set(str(src.with_name(src.stem + "_output.mp4")))

    def pick_output(self) -> None:
        path = filedialog.asksaveasfilename(title="Choose output file")
        if path:
            self.output_var.set(path)

    def append_log(self, text: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def run_job(self) -> None:
        src = self.input_var.get().strip()
        out = self.output_var.get().strip()
        if not src or not out:
            messagebox.showerror("Missing path", "Choose both input and output files.")
            return

        action = self.action_var.get()
        if action == "compress":
            cmd = [sys.executable, "-m", "localmedia.cli", "compress", src, "-o", out, "--crf", self.crf_var.get(), "--overwrite"]
        elif action == "convert":
            cmd = [sys.executable, "-m", "localmedia.cli", "convert", src, "--to", self.format_var.get(), "-o", out, "--overwrite"]
        else:
            cmd = [sys.executable, "-m", "localmedia.cli", "strip-metadata", src, "-o", out, "--overwrite"]

        self.status_var.set("Running locally...")
        self.append_log("$ " + " ".join(cmd))
        threading.Thread(target=self._worker, args=(cmd,), daemon=True).start()

    def _worker(self, cmd: list[str]) -> None:
        proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
        self.after(0, self.append_log, proc.stdout.strip())
        if proc.returncode == 0:
            self.after(0, self.status_var.set, "Completed. Output written locally.")
        else:
            self.after(0, self.status_var.set, f"Failed with exit code {proc.returncode}.")


def main() -> None:
    App().mainloop()


if __name__ == "__main__":
    main()
