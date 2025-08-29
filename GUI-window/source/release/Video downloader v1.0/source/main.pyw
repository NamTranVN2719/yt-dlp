import tkinter as tk
from tkinter import messagebox
import subprocess
import re
import os
import sys



Download_type = "mp4"  # Default
indicator_label = None

# Layout constants
LEFT_PCT = 0.56   # left content area (0..1). Trio + entry live here
MARGIN   = 0.02   # side margins

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
            # flush any remaining
            rest = process.stdout.read()
            if rest:
                log_text.config(state="normal")
                log_text.insert(tk.END, rest)
                log_text.see(tk.END)
                log_text.config(state="disabled")
            rc = process.returncode
            log_text.config(state="normal")
            log_text.insert(tk.END, f"\n--- Finished with exit code {rc} ---\n")
            log_text.see(tk.END)
            log_text.config(state="disabled")

    read_output()

# -------- Animation --------
def select_type(type_):
    global Download_type
    Download_type = type_
    update_indicator(type_)
    animate_circle(type_)

def update_indicator(type_: str):
    indicator_label.config(text=type_.upper())

def animate_circle(type_):
    btn_mp3.config(state="disabled")
    btn_mp4.config(state="disabled")

    if type_ == "mp4":
        start_color = (255, 0, 0)       # pure red center
        end_color   = (255, 128, 128)   # lighter red background
    else:
        start_color = (0, 170, 0)       # vivid green center
        end_color   = (128, 255, 128)   # lighter green background

    steps = 42
    delay_ms = 24

    def lerp(a: int, b: int, t: float) -> int:
        return int(a * (1 - t) + b * t)

    def expand(step=0):
        # compute left content region size each frame
        w = root.winfo_width()
        h = root.winfo_height()
        left_w_px = int(w * LEFT_PCT)
        cx = int(left_w_px * 0.5)                     # center in left area
        cy = int(h * 0.70)                            # around the trio row
        max_size = int(((left_w_px ** 2 + h ** 2) ** 0.5) * 2)

        if step < steps:
            t = step / (steps - 1)
            size = int(max_size * t)

            r = lerp(start_color[0], end_color[0], t)
            g = lerp(start_color[1], end_color[1], t)
            b = lerp(start_color[2], end_color[2], t)
            fill_color = f"#{r:02x}{g:02x}{b:02x}"

            canvas.delete("circle")
            canvas.create_oval(
                cx - size // 2, cy - size // 2,
                cx + size // 2, cy + size // 2,
                fill=fill_color, outline="#ffffff", width=8, tags="circle"
            )
            root.after(delay_ms, lambda: expand(step + 1))
        else:
            # set final background tint for the whole canvas
            final_color = f"#{end_color[0]:02x}{end_color[1]:02x}{end_color[2]:02x}"
            canvas.configure(bg=final_color)
            canvas.delete("circle")
            btn_mp3.config(state="normal")
            btn_mp4.config(state="normal")

    expand()

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
root.title("Video Downloader 1.0")
root.geometry("860x500")
root.configure(bg="#232946")

# Background canvas
canvas = tk.Canvas(root, bg="#ff4d61", highlightthickness=0)
canvas.place(x=0, y=0, relwidth=1, relheight=1)

# Entry frame (pink style) centered within the LEFT area
entry_frame = tk.Frame(root, bg="#eebbc3", bd=4, relief="ridge")
# place centered inside left region
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

# --- Bottom bar for MP4 / Indicator / MP3 (keeps spacing, shifted left) ---
bottom_bar = tk.Frame(root, bg="#eebbc3", bd=4, relief="ridge")
# span the left area width; sit near bottom
bottom_bar.place(relx=MARGIN, rely=0.85, anchor="w",
                 relwidth=LEFT_PCT - 2*MARGIN)

# use grid to keep equal spacing inside the left area
bottom_bar.columnconfigure(0, weight=1)
bottom_bar.columnconfigure(1, weight=1)
bottom_bar.columnconfigure(2, weight=1)

btn_mp4 = tk.Button(
    bottom_bar, text="MP4", command=lambda: select_type("mp4"),
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
    bottom_bar, text="MP3", command=lambda: select_type("mp3"),
    font=("Segoe UI", 13, "bold"),
    bg="#38b000", fg="#fff",
    bd=3, relief="raised", cursor="hand2", width=8
)
btn_mp3.grid(row=0, column=2, padx=8, pady=4, sticky="n")

# -------- Log panel (right side, pink style) --------
log_frame = tk.Frame(root, bg="#eebbc3", bd=4, relief="ridge")
# right area occupies the remaining width
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
