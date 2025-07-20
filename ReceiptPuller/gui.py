# dependencies
import subprocess
import sys
import os

def install_requirements():
    req_file = os.path.join(os.path.dirname(__file__), "requirements.txt")
    if os.path.exists(req_file):
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_file])
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install dependencies:\n{e}")
            sys.exit(1)
    else:
        print("⚠️ requirements.txt not found. Skipping dependency installation.")

install_requirements()

# gui.py
import tkinter as tk
from tkinter import filedialog, messagebox
from downloader import run_download
import tkinter.scrolledtext as st
import threading
import sys
import io
import queue
from tkinter import ttk

class QueueRedirector(io.TextIOBase):
    def __init__(self, queue):
        self.queue = queue

    def write(self, s):
        self.queue.put(s)

class UberDownloaderApp:
    def __init__(self, root):

        self.root = root
        self.root.title("Uber Receipt Downloader")

        self.csv_path = tk.StringVar()
        self.download_dir = tk.StringVar()

        # CSV File Picker
        tk.Label(root, text="CSV File:").pack(padx=10, pady=(10, 0), anchor='w')
        tk.Entry(root, textvariable=self.csv_path, width=60).pack(padx=10)
        tk.Button(root, text="Browse CSV", command=self.browse_csv).pack(padx=10, pady=(0, 10))

        # Folder Picker
        tk.Label(root, text="Download Folder:").pack(padx=10, anchor='w')
        tk.Entry(root, textvariable=self.download_dir, width=60).pack(padx=10)
        tk.Button(root, text="Browse Folder", command=self.browse_folder).pack(padx=10, pady=(0, 10))

        # Log Output
        tk.Label(root, text="Log:").pack(padx=10, anchor='w')
        self.log_box = st.ScrolledText(root, height=15, width=80, state='disabled')
        self.log_box.pack(padx=10, pady=(0, 10))

        # Redirect stdout to the log box
        self.log_queue = queue.Queue()
        sys.stdout = QueueRedirector(self.log_queue)
        sys.stderr = QueueRedirector(self.log_queue)
        self.update_log_box()

        # Progress Bar
        self.progress = ttk.Progressbar(root, orient='horizontal', length=400, mode='determinate')
        self.progress.pack(padx=10, pady=(5, 10))

        # Start Button
        tk.Button(root, text="Start Download", command=self.start_download, bg="green", fg="white").pack(padx=10, pady=20)

        # Cancel Button
        self.cancel_requested = False
        self.cancel_button = tk.Button(root, text="Cancel", command=self.cancel_download, state='disabled')
        self.cancel_button.pack(padx=10, pady=(0, 10))

    def browse_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV Files", "*.csv")])
        if path:
            self.csv_path.set(path)

    def browse_folder(self):
        path = filedialog.askdirectory()
        if path:
            self.download_dir.set(path)

    def start_download(self):
        csv = self.csv_path.get()
        folder = self.download_dir.get()

        if not csv or not folder:
            messagebox.showerror("Missing Input", "Please select both a CSV file and download folder.")
            return

        def run():
            try:
                self.cancel_requested = False
                self.cancel_button.config(state='normal')

                def update_progress(current, total):
                    self.progress['maximum'] = total
                    self.progress['value'] = current

                run_download(csv, folder, update_progress, lambda: self.cancel_requested)
                if not self.cancel_requested:
                    messagebox.showinfo("Done", "All receipts downloaded successfully!")
                else:
                    print("Download cancelled by user.")

            except Exception as e:
                print(f"❌ ERROR: {e}")
                messagebox.showerror("Error", f"An error occurred:\n{e}")
            finally:
                self.cancel_button.config(state='disabled')
                self.progress['value'] = 0

        threading.Thread(target=run, daemon=True).start()

    def cancel_download(self):
        self.cancel_requested = True
        self.cancel_button.config(state='disabled')
        print("Download cancelled by user.")

    def update_log_box(self):
        try:
            while True:
                line = self.log_queue.get_nowait()
                self.log_box.configure(state='normal')
                self.log_box.insert(tk.END, line)
                self.log_box.see(tk.END)
                self.log_box.configure(state='disabled')
        except queue.Empty:
            pass
        self.root.after(100, self.update_log_box)

if __name__ == "__main__":
    root = tk.Tk()
    app = UberDownloaderApp(root)
    root.mainloop()
