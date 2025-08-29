import tkinter as tk
from tkinter import messagebox
import subprocess
import re
import os
import sys
import itertools

Download_type = "mp4"  # Default
indicator_label = None

# Layout constants
LEFT_PCT = 0.56   # left content area (0..1). Trio + entry live here
MARGIN   = 0.02   # side margins

circle_id_counter = itertools.count()   # unique IDs for circles
COOLDOWN_MS = 1000                       # 0.5 second cooldown for MP3/MP4

# -------- URL handling --------
def normalize_url(raw: str) -> str | None:
    url = raw.strip()
    if url.startswith(("http://", "https://")):
        return url
    if re.match(r"^(?:[A-Za-z0-9-]+\.)+[A-Za-z]{2,}(?:/.*)?$", url):
        return "https://" + url
    return None

def handle_download():
    fixed = normalize_url(entry.get())
    if not fixed:
        messagebox.showerror("Invalid URL", "Please enter a valid link")
        return
    path = os.path.join(os.path.expanduser("~"), "Downloads")
    downloader_path = "downloader.exe"

    # Trigger animation with Download lock
    animate_circle(Download_type, lock_download=True)

    run_command(f'"{downloader_path}" -P "{path}" -t {Download_type} {fixed}')

# -------- Run external command with live log --------
def run_command(command: str):
    log_text.config(state="normal")
    log_text.delete("1.0", tk.END)
    log_text.insert(tk.END, f"Downloading in progress...\n")
    log_text.config(state="disabled")

    process = subprocess.Popen(
        command, shell=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1, universal_newlines=True
    )

    def read_output():
        if process.poll() is None:
            line = process.stdout.readline()
            if line:
                log_text.config(state="normal")
                log_text.insert(tk.END, line)
                log_text.see(tk.END)
                log_text.config(state="disabled")
            root.after(50, read_output)
        else:
            rest = process.stdout.read()
            if rest:
                log_text.config(state="normal")
                log_text.insert(tk.END, rest)
                log_text.see(tk.END)
                log_text.config(state="disabled")
            rc = process.returncode
            log_text.config(state="normal")
            log_text.insert(tk.END, f"\n--- Finished with exit code {rc} ---\n")
            if rc != 0:
                log_text.insert(tk.END, f"==============================================\n")
                log_text.insert(tk.END, f"Error occurred during download.\n")
                log_text.insert(tk.END, f"Ensure that the URL is valid and accessible.\n")
                log_text.insert(tk.END, f"Ensure that FFmpeg is installed and accessible in your PATH. Otherwise, your downloaded mp4 will have NO audio and mp3 downloading is NOT supported.\n")
                log_text.insert(tk.END, f"==============================================\n")
            else:
                log_text.insert(tk.END, f"==============================================\n")
                log_text.insert(tk.END, f"No issue found, the video will be saved to your Downloads folder as {Download_type}.\n")
                log_text.insert(tk.END, f"==============================================\n")
            log_text.config(state="disabled")
            log_text.see(tk.END)

    read_output()

# -------- Animation --------
def select_type(type_):
    global Download_type
    Download_type = type_
    update_indicator(type_)
    animate_circle(type_)

def update_indicator(type_: str):
    indicator_label.config(text=type_.upper())

def animate_circle(type_, lock_download=False):
    if lock_download:
        btn_download.config(state="disabled")

    if type_ == "mp4":
        start_color = (255, 0, 0)       # pure red center
        end_color   = (255, 128, 128)   # lighter red background
    else:
        start_color = (0, 170, 0)       # vivid green center
        end_color   = (128, 255, 128)   # lighter green background

    steps = 42
    delay_ms = 24
    tag = f"circle_{next(circle_id_counter)}"   # unique tag per animation

    def lerp(a: int, b: int, t: float) -> int:
        return int(a * (1 - t) + b * t)

    def expand(step=0):
        w = root.winfo_width()
        h = root.winfo_height()
        left_w_px = int(w * LEFT_PCT)
        cx = int(left_w_px * 0.5)
        cy = int(h * 0.70)
        max_size = int(((left_w_px ** 2 + h ** 2) ** 0.5) * 2)

        if step < steps:
            t = step / (steps - 1)
            size = int(max_size * t)

            r = lerp(start_color[0], end_color[0], t)
            g = lerp(start_color[1], end_color[1], t)
            b = lerp(start_color[2], end_color[2], t)
            fill_color = f"#{r:02x}{g:02x}{b:02x}"

            canvas.delete(tag)
            canvas.create_oval(
                cx - size // 2, cy - size // 2,
                cx + size // 2, cy + size // 2,
                fill=fill_color, outline="#ffffff", width=8, tags=tag
            )
            root.after(delay_ms, lambda: expand(step + 1))
        else:
            canvas.delete(tag)
            # Final tint follows the last selected type
            canvas.configure(bg=f"#{end_color[0]:02x}{end_color[1]:02x}{end_color[2]:02x}")
            if lock_download:
                btn_download.config(state="normal")

    expand()

# -------- Cooldown wrapper for MP3/MP4 --------
def type_clicked(type_):
    # disable both buttons for the cooldown duration
    btn_mp3.config(state="disabled")
    btn_mp4.config(state="disabled")
    # perform the selection + animation
    select_type(type_)
    # re-enable after cooldown
    root.after(COOLDOWN_MS, lambda: (btn_mp3.config(state="normal"),
                                     btn_mp4.config(state="normal")))

# -------- Hover effects --------
def add_hover(widget, base_bg, hover_bg, base_fg=None, hover_fg=None):
    def on_enter(e):
        widget.config(bg=hover_bg)
        if hover_fg is not None:
            widget.config(fg=hover_fg)
    def on_leave(e):
        widget.config(bg=base_bg)
        if base_fg is not None:
            widget.config(fg=base_fg)
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

# -------- UI --------
root = tk.Tk()
root.iconbitmap(default="ico.ico")
root.title("Video Downloader 1.1")
root.geometry("860x500")
root.configure(bg="#232946")

# Background canvas
canvas = tk.Canvas(root, bg="#ff4d61", highlightthickness=0)
canvas.place(x=0, y=0, relwidth=1, relheight=1)

# Entry frame
entry_frame = tk.Frame(root, bg="#eebbc3", bd=4, relief="ridge")
entry_frame.place(relx=LEFT_PCT/2, rely=0.08, anchor="n", relwidth=LEFT_PCT - 2*MARGIN)

title_label = tk.Label(
    entry_frame, text="Insert video link",
    font=("Segoe UI", 16, "bold"),
    bg="#eebbc3", fg="#232946", pady=10
)
title_label.pack()

entry = tk.Entry(
    entry_frame, width=35, font=("Segoe UI", 13),
    bg="#FFFFFF", fg="#232946",
    bd=3, relief="raised", justify="center"
)
entry.pack(padx=12, pady=14)
entry.bind("<Return>", lambda e: handle_download())

btn_download = tk.Button(
    entry_frame, text="Download", command=handle_download,
    font=("Segoe UI", 12, "bold"),
    bg="#FFFFFF", fg="#eebbc3",
    bd=3, relief="raised", activebackground="#FFFFFF",
    activeforeground="#eebbc3", cursor="hand2"
)
btn_download.pack(padx=12, pady=8)

# --- Bottom bar ---
bottom_bar = tk.Frame(root, bg="#eebbc3", bd=4, relief="ridge")
bottom_bar.place(relx=MARGIN, rely=0.85, anchor="w",
                 relwidth=LEFT_PCT - 2*MARGIN)

bottom_bar.columnconfigure(0, weight=1)
bottom_bar.columnconfigure(1, weight=1)
bottom_bar.columnconfigure(2, weight=1)

btn_mp4 = tk.Button(
    bottom_bar, text="MP4", command=lambda: type_clicked("mp4"),
    font=("Segoe UI", 13, "bold"),
    bg="#e63946", fg="#fff",
    bd=3, relief="raised", cursor="hand2", width=8
)
btn_mp4.grid(row=0, column=0, padx=8, pady=4, sticky="n")

indicator_label = tk.Label(
    bottom_bar, text="MP4",
    font=("Segoe UI", 12, "bold"),
    bg="#FFFFFF", fg="#ff5353",
    bd=3, relief="raised", padx=20, pady=8
)
indicator_label.grid(row=0, column=1, padx=8, pady=4, sticky="n")

btn_mp3 = tk.Button(
    bottom_bar, text="MP3", command=lambda: type_clicked("mp3"),
    font=("Segoe UI", 13, "bold"),
    bg="#38b000", fg="#fff",
    bd=3, relief="raised", cursor="hand2", width=8
)
btn_mp3.grid(row=0, column=2, padx=8, pady=4, sticky="n")

# -------- Log panel --------
log_frame = tk.Frame(root, bg="#eebbc3", bd=4, relief="ridge")
log_frame.place(relx=1 - MARGIN, rely=0.08, anchor="ne",
                relwidth=(1 - LEFT_PCT) - MARGIN, relheight=0.84)

log_title = tk.Label(
    log_frame, text="Download Log",
    font=("Segoe UI", 14, "bold"),
    bg="#eebbc3", fg="#232946"
)
log_title.pack(pady=4)

log_text = tk.Text(
    log_frame, wrap="word",
    font=("Consolas", 10),
    bg="#FFFFFF", fg="#232946",
    bd=3, relief="raised"
)
log_text.pack(expand=True, fill="both", padx=8, pady=8)
log_text.config(state="disabled")

# -------- Hovers --------
add_hover(btn_download, "#FFFFFF", "#f7f7f7", "#eebbc3", "#d498a4")
add_hover(btn_mp4, "#e63946", "#ff4d61", "#fff", "#fff")
add_hover(btn_mp3, "#38b000", "#46d100", "#fff", "#fff")
add_hover(indicator_label, "#FFFFFF", "#f7f7f7", "#ff435f", "#ff0033")

root.mainloop()
