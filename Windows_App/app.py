# Imports
import tkinter as tk
import customtkinter as ctk
from PIL import Image, ImageTk
import threading
from tkinter import filedialog, messagebox
import os

# Splash Screen while loading models
def initialize_app():
    global generate_store_embeddings, search, check_stores

    try:
        from helper import generate_store_embeddings, search, check_stores

    except ImportError as e:
        print(f"Error loading modules: {e}")
    finally:
        splash_root.destroy()

    launch_main_app()


# Main Application
def launch_main_app():
    # Set the appearance mode and default color theme
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    # Root
    root = ctk.CTk()
    root._state_before_windows_set_titlebar_color = "zoomed"
    root.title("AI Gallery")

    # Frames
    searchFrame = ctk.CTkFrame(root)
    image_frame = ctk.CTkScrollableFrame(root)
    progress_frame = ctk.CTkFrame(root, height=0)

    # Widgets
    slider_value_var = tk.IntVar(value=5)

    search_entry = ctk.CTkEntry(
        searchFrame,
        placeholder_text="Search",
        corner_radius=100,
        font=("Arial", 24),
        height=50,
    )
    search_entry.bind("<Return>", lambda event: load_button.invoke())

    slider = ctk.CTkSlider(
        searchFrame, from_=5, to=50, number_of_steps=45, variable=slider_value_var
    )

    load_button = ctk.CTkButton(
        searchFrame, text="Search", height=50, corner_radius=100
    )

    add_button = ctk.CTkButton(
        searchFrame,
        text="Add Images To App",
        height=50,
        corner_radius=100,
        fg_color="transparent",
        border_color="#1F538D",
        border_width=2,
    )

    slider_value_label1 = ctk.CTkLabel(
        searchFrame, text="Number of Images to Display: ", height=50
    )

    slider_value_label2 = ctk.CTkLabel(searchFrame, textvariable=slider_value_var)

    # Function to display images
    def display_images():
        if not check_stores():
            messagebox.showerror(
                "Error",
                "Please add images to the app first. Click on 'Add Images To App' button.",
            )
            return
        elif not search_entry.get():
            messagebox.showerror("Error", "Please enter a search query.")
            return

        def load_images():
            # Create overlay
            loading_overlay = ctk.CTkToplevel(root)
            loading_overlay.geometry(
                f"{root.winfo_width()}x{root.winfo_height()}+{root.winfo_x()+10}+{root.winfo_y()+10}"
            )
            loading_overlay.configure(bg="#000000")
            loading_overlay.attributes("-alpha", 0.8)

            # Loading text
            loading_circle = ctk.CTkLabel(
                loading_overlay,
                text="Loading...",
                font=("Arial", 24),
                text_color="white",
            )
            loading_circle.place(relx=0.5, rely=0.5, anchor="center")

            root.update()  # Update UI to show overlay

            try:
                top_k = int(slider.get())
                query = search_entry.get()
                search_entry.delete(0, "end")
                image_list = search(query, top_k)

                # Clear previous images
                for widget in image_frame.winfo_children():
                    widget.destroy()

                # Dynamically calculate image size
                frame_width = image_frame.winfo_width()
                images_per_row = 4
                image_width = frame_width // images_per_row

                row, col = 0, 0  # Row and column counters for grid placement

                for image_path in image_list:
                    try:
                        image = Image.open(image_path)
                        aspect_ratio = image.width / image.height
                        new_height = int(image_width / aspect_ratio)
                        image = image.resize(
                            (image_width, new_height), Image.Resampling.LANCZOS
                        )
                        photo = ImageTk.PhotoImage(image)

                        img_label = ctk.CTkLabel(image_frame, image=photo, text="")
                        img_label.image = photo  # Keep reference

                        # Place the image in the grid
                        img_label.grid(row=row, column=col, padx=10, pady=10)

                        # Update column and row counters
                        col += 1
                        if (
                            col >= images_per_row
                        ):  # When the row is filled, move to the next row
                            col = 0
                            row += 1

                    except Exception as e:
                        print(f"Error loading image: {e}")
            finally:
                image_frame._parent_canvas.yview_moveto(0.0)
                loading_overlay.destroy()  # Remove overlay
                root.update()

        # Run the image loading in a separate thread
        threading.Thread(target=load_images).start()

    # Function to add images to the vector base
    def add_images():
        if threading.active_count() > 1:
            messagebox.showwarning(
                "Warning",
                "Image addition is already in progress. Please start after the current process is completed.",
            )
            return

        def add_images_thread():
            progress_var = tk.DoubleVar(value=0)
            progress_bar = ctk.CTkProgressBar(progress_frame)
            progress_bar.set(0)
            progress_bar.pack(fill="x", padx=10, pady=10)

            def update_progress(progress):
                progress_var.set(progress)
                progress_bar.set(progress)
                root.update_idletasks()

            folder_path = filedialog.askdirectory()
            if folder_path:
                generate_store_embeddings(folder_path, update_progress)
                messagebox.showinfo("Success", "Images added successfully.")

            progress_bar.destroy()

        threading.Thread(target=add_images_thread).start()

    # Configure widgets and layout
    load_button.configure(command=display_images)
    add_button.configure(command=add_images)

    slider_value_label1.grid(row=1, column=1, padx=10, pady=10)
    slider_value_label2.grid(row=1, column=2, padx=10, pady=10)
    searchFrame.grid_columnconfigure(0, weight=9, uniform="equal")
    searchFrame.grid_columnconfigure(1, weight=2, uniform="equal")
    search_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew", columnspan=2)
    load_button.grid(row=0, column=2, padx=10, pady=10, sticky="ew")
    add_button.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
    slider.grid(row=1, column=3, padx=10, pady=10, sticky="e")

    searchFrame.pack(fill="x", padx=10, pady=10)
    progress_frame.pack(fill="x", padx=10, pady=(0, 10))
    image_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    # Run the main loop
    root.mainloop()


# Splash Screen
splash_root = tk.Tk()
splash_root.overrideredirect(True)
splash_root.update_idletasks()

screen_width = splash_root.winfo_screenwidth()
screen_height = splash_root.winfo_screenheight()
splash_root.configure(bg='black')
splash_root.attributes('-transparentcolor', 'black')

width = int(screen_width * 0.5)
height = int(screen_height * 0.5)

x = (screen_width // 2) - (width // 2)
y = (screen_height // 2) - (height // 2)

splash_root.geometry(f"{width}x{height}+{x}+{y}")

# Get the current file path
current_file_path = os.path.dirname(os.path.abspath(__file__))
splash_image_path = os.path.join(current_file_path, "images", "Splash.png")
image = Image.open(splash_image_path)

image_aspect_ratio = image.width / image.height
new_width = width
new_height = int(width / image_aspect_ratio)

if new_height > height:
    new_height = height
    new_width = int(height * image_aspect_ratio)

image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

splash_image = ImageTk.PhotoImage(image)

splash_label = tk.Label(splash_root, image=splash_image, bg="black")
splash_label.place(relwidth=1, relheight=1)

splash_root.after(100, initialize_app)

splash_root.mainloop()
