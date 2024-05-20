import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
import io
import os
import win32clipboard
import datetime
import random

DEFAULT_STYLES = [
    "anime", "cartoon", "photograph", "portrait",
    "illustration", "caricature", "hentai", "boudoir"
]

class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pollinations Image Generator")
        self.root.attributes("-topmost", True)

        # Predefined styles
        self.default_styles = DEFAULT_STYLES
        self.user_styles = self.load_user_styles()

        self.styles = self.default_styles + self.user_styles

        # Create the menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Add the "Options" menu
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        
        # Add a checkbutton to the "Options" menu
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.options_menu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.always_on_top_var, command=self.toggle_always_on_top)

        self.nologo_password_label = tk.Label(root, text="nologo Password (optional):")
        self.nologo_password_label.grid(row=0, column=0, sticky="e")

        self.nologo_password_entry = tk.Entry(root)
        self.nologo_password_entry.grid(row=0, column=1, sticky="w")

        self.label = tk.Label(root, text="Enter your prompt and click 'Generate Image':")
        self.label.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.prompt_entry = tk.Entry(root)
        self.prompt_entry.grid(row=2, column=0, columnspan=2, sticky="ew")

        self.private_var = tk.BooleanVar(value=True)
        self.private_checkbutton = tk.Checkbutton(root, text="Private", variable=self.private_var)
        self.private_checkbutton.grid(row=3, column=0, columnspan=2, sticky="w")

        self.seed_label = tk.Label(root, text="Seed (optional):")
        self.seed_label.grid(row=4, column=0, sticky="e")

        self.seed_entry = tk.Entry(root)
        self.seed_entry.grid(row=4, column=1, sticky="w")

        self.width_label = tk.Label(root, text="Width (optional):")
        self.width_label.grid(row=5, column=0, sticky="e")

        self.width_entry = tk.Entry(root)
        self.width_entry.grid(row=5, column=1, sticky="w")

        self.height_label = tk.Label(root, text="Height (optional):")
        self.height_label.grid(row=6, column=0, sticky="e")

        self.height_entry = tk.Entry(root)
        self.height_entry.grid(row=6, column=1, sticky="w")

        self.style_label = tk.Label(root, text="Visual Style:")
        self.style_label.grid(row=7, column=0, sticky="e")

        self.style_var = tk.StringVar()
        self.style_menu = tk.OptionMenu(root, self.style_var, *self.styles)
        self.style_menu.grid(row=7, column=1, sticky="w")

        self.custom_style_entry = tk.Entry(root)
        self.custom_style_entry.grid(row=8, column=0, columnspan=2, sticky="ew")
        self.custom_style_entry.insert(0, "Type custom style here and press Enter")
        self.custom_style_entry.bind("<Return>", self.add_custom_style)

        self.generate_button = tk.Button(root, text="Generate Image", command=self.generate_image)
        self.generate_button.grid(row=9, column=0, sticky="ew")

        self.copy_button = tk.Button(root, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.grid(row=9, column=1, sticky="ew")

        # Add a bottom border for easy resizing
        self.status_bar = tk.Label(root, text="", bg="grey", height=1)
        self.status_bar.grid(row=10, column=0, columnspan=2, sticky="ew")

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.grid(row=11, column=0, columnspan=2, sticky="nsew")

        self.image = None
        self.display_image_resized = None

        self.root.bind("<Configure>", self.resize_image)

        # Configure grid to make canvas expandable
        self.root.grid_rowconfigure(11, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.previous_width = self.root.winfo_width()
        self.previous_height = self.root.winfo_height()

        # Save settings on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.load_settings()

    def load_user_styles(self):
        user_styles = []
        if os.path.exists("user_styles.txt"):
            with open("user_styles.txt", "r") as file:
                user_styles = [line.strip() for line in file.readlines()]
        return user_styles

    def save_user_styles(self):
        with open("user_styles.txt", "w") as file:
            for style in self.user_styles:
                file.write(style + "\n")

    def add_custom_style(self, event=None):
        new_style = self.custom_style_entry.get().strip()
        if new_style and new_style not in self.styles:
            self.user_styles.append(new_style)
            self.styles.append(new_style)
            self.style_menu['menu'].add_command(label=new_style, command=tk._setit(self.style_var, new_style))
            self.save_user_styles()
            self.custom_style_entry.delete(0, tk.END)
            self.custom_style_entry.insert(0, "Type custom style here and press Enter")

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def generate_image(self):
        prompt = self.prompt_entry.get()
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt")
            return
        
        # Add visual style to the prompt if selected
        style = self.style_var.get()
        if style:
            prompt += f" {style}"
        
        nologo_password = self.nologo_password_entry.get()
        if nologo_password:
            nologo_param = f"nologo={nologo_password}"
        else:
            nologo_param = "nologo=true"
        
        params = [nologo_param]
        
        if self.private_var.get():
            params.append("private=true")
        
        seed = self.seed_entry.get()
        if seed and seed != '-1':
            params.append(f"seed={seed}")
        elif seed == '-1':
            params.append(f"seed={random.randint(0, 99999)}") # Use a random seed if -1
        
        width = self.width_entry.get()
        if width:
            params.append(f"width={width}")
        
        height = self.height_entry.get()
        if height:
            params.append(f"height={height}")
        
        query_string = "&".join(params)
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}?{query_string}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()

            self.image = Image.open(io.BytesIO(response.content))
            self.display_image(self.image)
            self.save_image(self.image)

        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve the image. Error: {e}")

    def display_image(self, image):
        self.canvas.delete("all")
        self.display_image_resized = self.resize_proportionally(image)
        self.tk_image = ImageTk.PhotoImage(self.display_image_resized)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def resize_image(self, event):
        if self.image:
            self.display_image(self.image)

    def resize_proportionally(self, image):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width, image_height = image.size

        ratio = min(canvas_width / image_width, canvas_height / image_height)
        new_width = int(image_width * ratio)
        new_height = int(image_height * ratio)

        return image.resize((new_width, new_height), Image.LANCZOS)

    def save_image(self, image):
        if not os.path.exists('./GENERATED'):
            os.makedirs('./GENERATED')
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        save_path = f"./GENERATED/Image-{timestamp}.png"
        image.save(save_path, "PNG")
        self.saved_image_path = save_path

    def copy_to_clipboard(self):
        if self.saved_image_path:
            image = Image.open(self.saved_image_path)
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
            data = output.getvalue()[14:]
            output.close()
            win32clipboard.OpenClipboard()
            win32clipboard.EmptyClipboard()
            win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
            win32clipboard.CloseClipboard()
        else:
            messagebox.showerror("Error", "No image to copy. Generate an image first.")

    def load_settings(self):
        if os.path.exists("settings.txt"):
            with open("settings.txt", "r") as file:
                settings = file.read().splitlines()
                if settings:
                    self.nologo_password_entry.insert(0, settings[0])
                    self.private_var.set(settings[1] == 'True')
                    self.seed_entry.insert(0, settings[2])
                    self.width_entry.insert(0, settings[3])
                    self.height_entry.insert(0, settings[4])
                    self.style_var.set(settings[5])

    def save_settings(self):
        with open("settings.txt", "w") as file:
            file.write(f"{self.nologo_password_entry.get()}\n")
            file.write(f"{self.private_var.get()}\n")
            file.write(f"{self.seed_entry.get()}\n")
            file.write(f"{self.width_entry.get()}\n")
            file.write(f"{self.height_entry.get()}\n")
            file.write(f"{self.style_var.get()}\n")

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()
