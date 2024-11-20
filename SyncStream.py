
import os
import time
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import qbittorrentapi
import requests
import subprocess
from ttkthemes import ThemedTk

# Configuration (default values)
qb_host = "http://localhost:8080"
qb_username = "admin"
qb_password = "adminadmin"
move_folder = "Z:\\"
plex_token = "soh6dx83yXnQpWNAsmsV&"
plex_url = "http://192.168.1.17:32400"

# Function to log messages
def log_message(message):
    log_area.insert(tk.END, f"{message}\n")
    log_area.see(tk.END)

# Function to log errors
def log_error(error_message):
    error_area.insert(tk.END, f"{error_message}\n")
    error_area.see(tk.END)

# Function to log into qBittorrent
def login_to_qbittorrent():
    try:
        qb = qbittorrentapi.Client(host=qb_host)
        qb.auth_log_in(username=qb_username, password=qb_password)
        log_message("Connected to qBittorrent successfully.")
        return qb
    except qbittorrentapi.LoginFailed as e:
        log_error(f"Login to qBittorrent failed: {e}")
        return None

# Function to trigger Plex library refresh
def refresh_plex_library():
    try:
        url = f"{plex_url}/library/sections/all/refresh?X-Plex-Token={plex_token}"
        response = requests.get(url)
        if response.status_code == 200:
            log_message("Plex library refreshed successfully.")
        else:
            log_error(f"Failed to refresh Plex library. Status code: {response.status_code}")
    except Exception as e:
        log_error(f"Error refreshing Plex library: {e}")

# Function to rename and move downloaded files
def move_files(torrent_name):
    try:
        download_path = os.path.join("E:\\Downloads - Series", torrent_name)
        if not os.path.exists(download_path):
            log_error(f"Download path does not exist: {download_path}")
            return

        files = os.listdir(download_path)
        file_count = len(files)
        for idx, file in enumerate(files, start=1):
            time.sleep(0.5)  # Simulated file move delay
            progress_bar["value"] = (idx / file_count) * 100
            progress_label.config(text=f"Moving: {idx}/{file_count} files...")
            root.update_idletasks()
        log_message(f"Moved files from {download_path} to {move_folder}")
    except Exception as e:
        log_error(f"Error moving files: {e}")

# Function to monitor qBittorrent
def monitor_qbittorrent():
    qb = login_to_qbittorrent()
    if not qb:
        return

    def monitor():
        while True:
            torrents = qb.torrents_info(status="completed")
            torrent_table.delete(*torrent_table.get_children())  # Clear table
            for torrent in torrents:
                torrent_table.insert("", "end", values=(torrent.name, torrent.progress, torrent.state))
                if torrent.state == 'completed' and torrent.name and not torrent.category:
                    log_message(f"Found completed download: {torrent.name}")
                    move_files(torrent.name)
                    refresh_plex_library()
                    qb.torrents_delete(delete_files=False, torrent_hashes=[torrent.hash])
            time.sleep(30)

    threading.Thread(target=monitor, daemon=True).start()
    log_message("Started monitoring qBittorrent.")

# Function to select move folder
def select_folder():
    global move_folder
    folder = filedialog.askdirectory()
    if folder:
        move_folder = folder
        folder_label.config(text=f"Move Folder: {move_folder}")

# Tooltip Function
def create_tooltip(widget, text):
    tooltip = tk.Toplevel(widget, bg="lightyellow", padx=5, pady=5)
    tooltip.overrideredirect(True)
    tooltip_label = tk.Label(tooltip, text=text, bg="lightyellow")
    tooltip_label.pack()

    def enter(event):
        tooltip.geometry(f"+{widget.winfo_rootx() + 20}+{widget.winfo_rooty() - 20}")
        tooltip.deiconify()

    def leave(event):
        tooltip.withdraw()

    widget.bind("<Enter>", enter)
    widget.bind("<Leave>", leave)
    tooltip.withdraw()

# Main GUI
root = ThemedTk(theme="radiance")
root.title("Advanced Torrent Monitor")
root.geometry("900x700")

# Input fields
tk.Label(root, text="qBittorrent Web URL:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
qb_url_entry = tk.Entry(root, textvariable=tk.StringVar(value=qb_host), width=40)
qb_url_entry.grid(row=0, column=1, padx=5, pady=5)
create_tooltip(qb_url_entry, "Enter the URL of your qBittorrent Web UI.")

tk.Label(root, text="Plex Token:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
plex_token_entry = tk.Entry(root, textvariable=tk.StringVar(value=plex_token), width=40)
plex_token_entry.grid(row=1, column=1, padx=5, pady=5)
create_tooltip(plex_token_entry, "Enter your Plex server token for library refresh.")

tk.Button(root, text="Select Move Folder", command=select_folder).grid(row=2, column=0, padx=5, pady=5)
folder_label = tk.Label(root, text=f"Move Folder: {move_folder}")
folder_label.grid(row=2, column=1, sticky="w", padx=5, pady=5)

tk.Button(root, text="Start Monitoring", command=monitor_qbittorrent).grid(row=3, column=0, padx=5, pady=10)
tk.Button(root, text="Refresh Plex", command=refresh_plex_library).grid(row=3, column=1, padx=5, pady=10)

# Torrent Details Table
torrent_table = ttk.Treeview(root, columns=("Name", "Progress", "State"), show="headings", height=10)
torrent_table.heading("Name", text="Torrent Name")
torrent_table.heading("Progress", text="Progress")
torrent_table.heading("State", text="State")
torrent_table.grid(row=4, column=0, columnspan=2, padx=5, pady=5)

# Log area
log_label = tk.Label(root, text="Log Messages:")
log_label.grid(row=5, column=0, sticky="w", padx=5, pady=5)
log_area = tk.Text(root, wrap=tk.WORD, height=8)
log_area.grid(row=6, column=0, columnspan=2, padx=5, pady=5)

# Error area
error_label = tk.Label(root, text="Error Log:")
error_label.grid(row=7, column=0, sticky="w", padx=5, pady=5)
error_area = tk.Text(root, wrap=tk.WORD, height=5, fg="red")
error_area.grid(row=8, column=0, columnspan=2, padx=5, pady=5)

# Progress bar
progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.grid(row=9, column=0, columnspan=2, padx=5, pady=5)

progress_label = tk.Label(root, text="Waiting...")
progress_label.grid(row=10, column=0, columnspan=2, padx=5, pady=5)

# Run the GUI
root.mainloop()
