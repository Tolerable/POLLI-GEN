import tkinter as tk
from tkinter import messagebox, filedialog
from PIL import Image, ImageTk
import requests
import io
import os

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

        self.generate_button = tk.Button(root, text="Generate Image", command=self.generate_image)
        self.generate_button.grid(row=2, column=0, sticky="ew")

        self.save_button = tk.Button(root, text="Save Image", command=self.save_image)
        self.save_button.grid(row=2, column=1, sticky="ew")

        # Add a bottom border for easy resizing
        self.status_bar = tk.Label(root, text="", bg="grey", height=1)
        self.status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.grid(row=4, column=0, columnspan=2, sticky="nsew")

        self.image = None
        self.display_image_resized = None

        self.root.bind("<Configure>", self.resize_image)

        # Configure grid to make canvas expandable
        self.root.grid_rowconfigure(4, weight=1)
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
        
        try:
            url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(prompt)}"
            response = requests.get(url)
            response.raise_for_status()

            self.image = Image.open(io.BytesIO(response.content))
            self.display_image(self.image)

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

    def save_image(self):
        if self.image:
            if not os.path.exists('./GENERATED'):
                os.makedirs('./GENERATED')
            save_path = filedialog.asksaveasfilename(defaultextension=".png", initialdir='./GENERATED', filetypes=[("PNG files", "*.png")])
            if save_path:
                self.image.save(save_path, "PNG")
                messagebox.showinfo("Success", f"Image saved as {save_path}")
        else:
            messagebox.showerror("Error", "No image to save. Generate an image first.")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()
