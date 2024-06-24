import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pytube import YouTube, exceptions
import threading
import requests
from PIL import Image, ImageTk
import io
from datetime import datetime
import time

class ColoredProgressBar(ttk.Frame):
    def set_color(self, color):
        self.color = color
        style = ttk.Style()
        style.configure("TProgressbar", troughcolor=self.color, background=self.color)
        self.progress.config(style="TProgressbar")

    def __init__(self, master=None, **kw):
        super().__init__(master, **kw)
        self.color = '#3498db'
        self.progress = ttk.Progressbar(self, length=700, mode='determinate', style="TProgressbar", orient=tk.HORIZONTAL)
        self.progress.pack(fill="both", expand=True)

class YouTubeDownloaderApp:
    def __init__(self, master):
        self.master = master
        self.master.title("YouTube Video Downloader")
        self.master.geometry("800x600")
        self.download_history = []

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TProgressbar", thickness=20, troughcolor='#3498db')

        self.frame = ttk.Frame(self.master)
        self.frame.place(relx=0.5, rely=0.5, anchor="center")

        self.create_widgets()
        self.progress_bar = ColoredProgressBar(self.master)
        self.progress_bar.place(relx=0.5, rely=0.9, anchor="center")

    def create_widgets(self):
        self.url_label = ttk.Label(self.frame, text="Enter YouTube URL:")
        self.url_label.grid(row=0, column=0, padx=10, pady=10, sticky="w")
        self.url_entry = ttk.Entry(self.frame, width=50, style="TEntry")
        self.url_entry.grid(row=0, column=1, padx=10, pady=10)

        self.save_path_label = ttk.Label(self.frame, text="Enter Save Path:")
        self.save_path_label.grid(row=1, column=0, padx=10, pady=10, sticky="w")
        self.save_path_entry = ttk.Entry(self.frame, width=50, style="TEntry")
        self.save_path_entry.grid(row=1, column=1, padx=10, pady=10)
        self.browse_button = ttk.Button(self.frame, text="Browse", command=self.browse_save_path, style="TButton")
        self.browse_button.grid(row=1, column=2, padx=10, pady=10)

        self.quality_label = ttk.Label(self.frame, text="Select Video Quality:")
        self.quality_label.grid(row=2, column=0, padx=10, pady=10, sticky="w")
        self.qualities = ["720p", "480p", "360p"]
        self.quality_var = tk.StringVar(self.master)
        self.quality_var.set(self.qualities[0])
        self.quality_menu = ttk.OptionMenu(self.frame, self.quality_var, *self.qualities)
        self.quality_menu.grid(row=2, column=1, padx=10, pady=10, sticky="w")

        self.format_label = ttk.Label(self.frame, text="Select Video Format:")
        self.format_label.grid(row=3, column=0, padx=10, pady=10, sticky="w")
        self.formats = ["mp4", "webm"]
        self.format_var = tk.StringVar(self.master)
        self.format_var.set(self.formats[0])
        self.format_menu = ttk.OptionMenu(self.frame, self.format_var, *self.formats)
        self.format_menu.grid(row=3, column=1, padx=10, pady=10, sticky="w")

        self.download_button = ttk.Button(self.frame, text="Download Video", command=self.download_video, style="TButton")
        self.download_button.grid(row=4, column=0, columnspan=3, pady=10)

        self.video_details_label = ttk.Label(self.frame, text="Video Details:")
        self.video_details_label.grid(row=5, column=0, padx=10, pady=10, sticky="w")

        self.video_details_text = tk.Text(self.frame, width=60, height=5, wrap=tk.WORD, state="disabled")
        self.video_details_text.grid(row=5, column=1, columnspan=2, padx=10, pady=10)

        self.thumbnail_label = ttk.Label(self.frame, text="Thumbnail:")
        self.thumbnail_label.grid(row=6, column=0, padx=10, pady=10, sticky="w")
        self.thumbnail_canvas = tk.Canvas(self.frame, width=160, height=90, bg="white", borderwidth=2, relief="solid")
        self.thumbnail_canvas.grid(row=6, column=1, padx=10, pady=10)

        self.status_label = ttk.Label(self.frame, text="")
        self.status_label.grid(row=7, column=0, columnspan=3, pady=10)

        self.history_label = ttk.Label(self.frame, text="Download History:")
        self.history_label.grid(row=8, column=0, padx=10, pady=10, sticky="w")

        self.history_text = tk.Text(self.frame, width=60, height=10, wrap=tk.WORD, state="disabled")
        self.history_text.grid(row=8, column=1, columnspan=2, padx=10, pady=10)

    def browse_save_path(self):
        save_path = filedialog.askdirectory()
        self.save_path_entry.delete(0, 'end')
        self.save_path_entry.insert(0, save_path)

    def download_video(self):
        video_url = self.url_entry.get()
        save_path = self.save_path_entry.get()
        selected_quality = self.quality_var.get()
        selected_format = self.format_var.get()

        if not video_url or not save_path:
            messagebox.showerror("Input Error", "Please provide both YouTube URL and Save Path.")
            return

        try:
            yt = YouTube(video_url, on_progress_callback=self.update_progress)
            video_stream = yt.streams.filter(res=selected_quality, file_extension=selected_format).first()

            if video_stream:
                download_thread = threading.Thread(target=self.download_threaded, args=(yt, video_stream, save_path))
                download_thread.start()
                self.show_video_details(yt)
                self.show_thumbnail(yt.thumbnail_url)
            else:
                self.status_label.config(text="Error: No matching video stream found.")
        except exceptions.RegexMatchError:
            self.status_label.config(text="Error: Invalid YouTube URL.")
        except Exception as e:
            self.status_label.config(text=f"Error: {e}")

    def download_threaded(self, yt, video_stream, save_path):
        try:
            self.progress_bar.set_color('#e74c3c')
            self.progress_bar.progress.start()
            start_time = time.time()

            video_stream.download(output_path=save_path)
            end_time = time.time()
            download_time = end_time - start_time

            self.master.after(0, lambda: self.on_download_complete(yt, save_path, download_time))

        except Exception as e:
            self.master.after(0, lambda: self.status_label.config(text=f"Error: {e}"))
        finally:
            self.progress_bar.progress.stop()

    def on_download_complete(self, yt, save_path, download_time):
        self.status_label.config(text=f"Video '{yt.title}' downloaded successfully in {download_time:.2f} seconds!")
        self.add_to_history(yt.title, save_path)
        self.progress_bar.progress["value"] = 0

    def update_progress(self, stream, chunk, bytes_remaining):
        bytes_downloaded = stream.filesize - bytes_remaining
        percentage = int(bytes_downloaded / stream.filesize * 100)
        self.master.after(0, lambda: self.progress_bar.progress.config(value=percentage))

    def show_video_details(self, yt):
        details = (f"Title: {yt.title}\n"
                   f"Author: {yt.author}\n"
                   f"Duration: {yt.length} seconds\n"
                   f"Views: {yt.views}\n"
                   f"Rating: {yt.rating}")

        self.video_details_text.config(state="normal")
        self.video_details_text.delete(1.0, tk.END)
        self.video_details_text.insert(tk.END, details)
        self.video_details_text.config(state="disabled")

    def show_thumbnail(self, thumbnail_url):
        try:
            response = requests.get(thumbnail_url)
            img_data = response.content
            img = Image.open(io.BytesIO(img_data))
            img.thumbnail((160, 90))
            img_tk = ImageTk.PhotoImage(img)
            self.thumbnail_canvas.create_image(0, 0, anchor="nw", image=img_tk)
            self.thumbnail_canvas.image = img_tk
        except Exception as e:
            print("Error:", e)

    def add_to_history(self, title, save_path):
        download_info = {
            "title": title,
            "download_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "save_path": save_path
        }
        self.download_history.append(download_info)
        self.update_history_display()

    def update_history_display(self):
        self.history_text.config(state="normal")
        self.history_text.delete(1.0, tk.END)
        for video in self.download_history:
            self.history_text.insert(tk.END, f"Title: {video['title']}\n")
            self.history_text.insert(tk.END, f"Download Date: {video['download_date']}\n")
            self.history_text.insert(tk.END, f"Save Path: {video['save_path']}\n\n")
        self.history_text.config(state="disabled")

def main():
    root = tk.Tk()
    app = YouTubeDownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
