import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import requests
import io
import os
import win32clipboard
import datetime

class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pollinations Image Generator")
        self.root.attributes("-topmost", True)

        # Create the menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Add the "Options" menu
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        
        # Add a checkbutton to the "Options" menu
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.options_menu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.always_on_top_var, command=self.toggle_always_on_top)

        self.label = tk.Label(root, text="Enter your prompt and click 'Generate Image':")
        self.label.grid(row=0, column=0, columnspan=2, sticky="ew")

        self.prompt_entry = tk.Entry(root)
        self.prompt_entry.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.private_var = tk.BooleanVar()
        self.no_logo_var = tk.BooleanVar()

        self.private_checkbutton = tk.Checkbutton(root, text="Private", variable=self.private_var)
        self.private_checkbutton.grid(row=2, column=0, sticky="w")

        self.no_logo_checkbutton = tk.Checkbutton(root, text="No Logo", variable=self.no_logo_var)
        self.no_logo_checkbutton.grid(row=2, column=1, sticky="w")

        self.seed_label = tk.Label(root, text="Seed (optional):")
        self.seed_label.grid(row=3, column=0, sticky="e")

        self.seed_entry = tk.Entry(root)
        self.seed_entry.grid(row=3, column=1, sticky="w")

        self.width_label = tk.Label(root, text="Width (optional):")
        self.width_label.grid(row=4, column=0, sticky="e")

        self.width_entry = tk.Entry(root)
        self.width_entry.grid(row=4, column=1, sticky="w")

        self.height_label = tk.Label(root, text="Height (optional):")
        self.height_label.grid(row=5, column=0, sticky="e")

        self.height_entry = tk.Entry(root)
        self.height_entry.grid(row=5, column=1, sticky="w")

        self.generate_button = tk.Button(root, text="Generate Image", command=self.generate_image)
        self.generate_button.grid(row=6, column=0, sticky="ew")

        self.copy_button = tk.Button(root, text="Copy to Clipboard", command=self.copy_to_clipboard)
        self.copy_button.grid(row=6, column=1, sticky="ew")

        # Add a bottom border for easy resizing
        self.status_bar = tk.Label(root, text="", bg="grey", height=1)
        self.status_bar.grid(row=7, column=0, columnspan=2, sticky="ew")

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.grid(row=8, column=0, columnspan=2, sticky="nsew")

        self.image = None
        self.display_image_resized = None

        self.root.bind("<Configure>", self.resize_image)

        # Configure grid to make canvas expandable
        self.root.grid_rowconfigure(8, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)

        self.previous_width = self.root.winfo_width()
        self.previous_height = self.root.winfo_height()

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())

    def generate_image(self):
        prompt = self.prompt_entry.get()
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt")
            return

        params = []
        
        if self.private_var.get():
            params.append("private=true")
        
        if self.no_logo_var.get():
            params.append("no_logo=true")
        
        seed = self.seed_entry.get()
        if seed:
            params.append(f"seed={seed}")
        
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
            messagebox.showinfo("Success", "Image copied to clipboard.")
        else:
            messagebox.showerror("Error", "No image to copy. Generate an image first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()
