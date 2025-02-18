import os
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk  # For background image
import pygame
import random

# Initialize pygame mixer
pygame.mixer.init()

# Functionality
def play_song():
    selected_song = song_listbox.get(tk.ACTIVE)
    if not selected_song:
        messagebox.showinfo("No Song Selected", "Please select a song to play.")
        return
    song_path = os.path.join(music_folder, selected_song)
    pygame.mixer.music.load(song_path)
    pygame.mixer.music.play()
    status_label.config(text=f"Playing: {selected_song}")

def stop_song():
    pygame.mixer.music.stop()
    status_label.config(text="Stopped")

def pause_song():
    pygame.mixer.music.pause()
    status_label.config(text="Paused")

def resume_song():
    pygame.mixer.music.unpause()
    status_label.config(text="Playing")

def load_songs():
    global music_folder
    music_folder = filedialog.askdirectory(title="Select Music Folder")
    if not music_folder:
        return
    song_listbox.delete(0, tk.END)
    songs = [f for f in os.listdir(music_folder) if f.endswith(('.mp3', '.wav'))]
    for song in songs:
        song_listbox.insert(tk.END, song)
    if not songs:
        messagebox.showinfo("No Songs Found", "No .mp3 or .wav files found in the selected folder.")

def set_volume(val):
    """Set the volume based on the slider value."""
    volume = int(val) / 100  # Scale to 0.0 - 1.0
    pygame.mixer.music.set_volume(volume)
    status_label.config(text=f"Volume: {int(val)}%")

def move_up():
    """Move the selected song up in the list."""
    current_selection = song_listbox.curselection()
    if current_selection:
        index = current_selection[0]
        if index > 0:
            song = song_listbox.get(index)
            song_listbox.delete(index)
            song_listbox.insert(index - 1, song)
            song_listbox.selection_set(index - 1)

def move_down():
    """Move the selected song down in the list."""
    current_selection = song_listbox.curselection()
    if current_selection:
        index = current_selection[0]
        if index < song_listbox.size() - 1:
            song = song_listbox.get(index)
            song_listbox.delete(index)
            song_listbox.insert(index + 1, song)
            song_listbox.selection_set(index + 1)

def shuffle_play():
    """Play a random song from the list."""
    size = song_listbox.size()
    if size == 0:
        messagebox.showinfo("No Songs Found", "Please load songs first.")
        return
    random_index = random.randint(0, size - 1)
    song_listbox.selection_clear(0, tk.END)
    song_listbox.selection_set(random_index)
    play_song()

def next_song():
    """Play the next song in the list."""
    current_selection = song_listbox.curselection()
    if current_selection:
        index = current_selection[0]
        next_index = (index + 1) % song_listbox.size()  # Loop back to the start if at the end
        song_listbox.selection_clear(0, tk.END)
        song_listbox.selection_set(next_index)
        play_song()
    else:
        messagebox.showinfo("No Song Selected", "Please select or load a song first.")

# UI Setup
root = tk.Tk()
root.title("Advanced Music Player")
root.geometry("500x500")
root.resizable(False, False)

# Add background image
background_image_path = "background.jpg"  # Replace with your image path
if os.path.exists(background_image_path):
    bg_image = Image.open(background_image_path)
    bg_image = bg_image.resize((500, 500), Image.ANTIALIAS)
    bg_photo = ImageTk.PhotoImage(bg_image)
    bg_label = tk.Label(root, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)

# Song Listbox
song_listbox = tk.Listbox(root, width=50, height=15)
song_listbox.pack(pady=10)

# Buttons
button_frame = tk.Frame(root, bg="lightgray")
button_frame.pack()

load_button = tk.Button(button_frame, text="Load Songs", command=load_songs, width=10)
play_button = tk.Button(button_frame, text="Play", command=play_song, width=10)
pause_button = tk.Button(button_frame, text="Pause", command=pause_song, width=10)
resume_button = tk.Button(button_frame, text="Resume", command=resume_song, width=10)
stop_button = tk.Button(button_frame, text="Stop", command=stop_song, width=10)
next_button = tk.Button(button_frame, text="Next", command=next_song, width=10)

load_button.grid(row=0, column=0, padx=5, pady=5)
play_button.grid(row=0, column=1, padx=5, pady=5)
pause_button.grid(row=0, column=2, padx=5, pady=5)
resume_button.grid(row=1, column=0, padx=5, pady=5)
stop_button.grid(row=1, column=1, padx=5, pady=5)
next_button.grid(row=1, column=2, padx=5, pady=5)

# Shuffle and Move Buttons
extra_button_frame = tk.Frame(root, bg="lightgray")
extra_button_frame.pack()

shuffle_button = tk.Button(extra_button_frame, text="Shuffle Play", command=shuffle_play, width=10)
up_button = tk.Button(extra_button_frame, text="Move Up", command=move_up, width=10)
down_button = tk.Button(extra_button_frame, text="Move Down", command=move_down, width=10)

shuffle_button.grid(row=0, column=0, padx=5, pady=5)
up_button.grid(row=0, column=1, padx=5, pady=5)
down_button.grid(row=0, column=2, padx=5, pady=5)

# Volume Control
volume_label = tk.Label(root, text="Volume", bg="lightgray")
volume_label.pack(pady=5)

Volume = tk.Scale(root, from_=0, to=100, orient=tk.HORIZONTAL, command=set_volume)
Volume.set(50)  # Set initial volume to 50%
Volume.pack()

# Status Label
status_label = tk.Label(root, text="Welcome to Advanced Music Player", bg="lightgray", anchor="center")
status_label.pack(pady=10)

# Run the Application
root.mainloop()
