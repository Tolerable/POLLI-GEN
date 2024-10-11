import tkinter as tk
from tkinter import messagebox, filedialog, simpledialog
from PIL import Image, ImageTk
import requests
import io
import os
import datetime
import random
import asyncio
import aiohttp
import threading
import hashlib
import urllib.parse
import webbrowser
import json
from tkinter import ttk

# Define the current version of the script
CURRENT_VERSION = "1.3.161"

class WrapTreatmentDialog(tk.Toplevel):
    def __init__(self, parent, name=None, pre=None, post=None):
        super().__init__(parent)
        self.title("Edit Wrap Treatment" if name else "New Wrap Treatment")
        self.result = None

        tk.Label(self, text="Name:").grid(row=0, column=0, sticky="w")
        self.name_entry = tk.Entry(self)
        self.name_entry.grid(row=0, column=1)
        if name:
            self.name_entry.insert(0, name)
            self.name_entry.config(state='readonly')

        tk.Label(self, text="Pre-wrap:").grid(row=1, column=0, sticky="w")
        self.pre_text = tk.Text(self, height=5, width=50)
        self.pre_text.grid(row=1, column=1)
        if pre:
            self.pre_text.insert(tk.END, pre)

        tk.Label(self, text="Post-wrap:").grid(row=2, column=0, sticky="w")
        self.post_text = tk.Text(self, height=5, width=50)
        self.post_text.grid(row=2, column=1)
        if post:
            self.post_text.insert(tk.END, post)

        tk.Button(self, text="Save", command=self.save).grid(row=3, column=0, columnspan=2)
        tk.Button(self, text="Cancel", command=self.cancel).grid(row=4, column=0, columnspan=2)

    def save(self):
        name = self.name_entry.get()
        pre = self.pre_text.get("1.0", tk.END).strip()
        post = self.post_text.get("1.0", tk.END).strip()
        if name and (pre or post):
            self.result = (name, pre, post)
            self.destroy()

    def cancel(self):
        self.destroy()

class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Polli-Gen Image Generator")
        self.root.attributes("-topmost", True)
        self.root.geometry("520x880")
        self.root.resizable(False, False)

        self.save_path = os.path.abspath('./GENERATED')
        self.timer_running = False
        self.generating_image = False
        self.generated_images = []
        self.backup_path = ""
        self.prompt_history = self.load_prompt_history()

        self.default_styles = ["Empty"]
        self.user_styles = self.load_styles_from_file()
        self.styles = self.default_styles + [style.split(":", 1)[0] for style in self.user_styles]

        self.wrap_treatments = self.load_wrap_treatments()

        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.options_menu.add_command(label="Set Save Path", command=self.set_save_path)
        self.options_menu.add_command(label="Set Backup Path", command=self.set_backup_path)
        self.options_menu.add_command(label="Update Script", command=self.update_script)
        self.options_menu.add_separator()
        self.options_menu.add_command(label="About", command=self.show_about_dialog)

        self.use_negative_var = tk.BooleanVar(value=False)
        self.options_menu.add_checkbutton(label="Use Negative Styles", onvalue=True, offvalue=False, variable=self.use_negative_var)

        self.nologo_password_label = tk.Label(self.options_menu, text="No Logo Password (optional):")
        self.nologo_password_label.pack()
        self.nologo_password_entry = tk.Entry(self.options_menu)
        self.nologo_password_entry.pack()
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.options_menu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.always_on_top_var, command=self.toggle_always_on_top)

        self.prompt_entry = tk.Entry(root, justify='center')
        self.prompt_entry.insert(0, "Enter your prompt and click 'GENERATE'")
        self.prompt_entry.config(fg='grey')
        self.prompt_entry.grid(row=0, column=0, columnspan=6, sticky="ew")
        self.prompt_entry.bind("<Return>", self.on_generate_button_click)
        self.prompt_entry.bind("<FocusIn>", self.on_entry_click)
        self.prompt_entry.bind("<FocusOut>", self.on_focusout)

        self.prompt_history_combobox = ttk.Combobox(root, values=self.prompt_history)
        self.prompt_history_combobox.grid(row=1, column=0, columnspan=6, sticky="ew")
        self.prompt_history_combobox.bind("<<ComboboxSelected>>", self.load_prompt_from_history)

        self.enhance_var = tk.BooleanVar(value=False)
        self.enhance_checkbutton = tk.Checkbutton(root, text="Enhance Image", variable=self.enhance_var)
        self.enhance_checkbutton.grid(row=2, column=0, columnspan=2, sticky="we")
        self.private_var = tk.BooleanVar(value=True)
        self.private_checkbutton = tk.Checkbutton(root, text="Private", variable=self.private_var)
        self.private_checkbutton.grid(row=2, column=2, columnspan=2, sticky="we")

        self.seed_label = tk.Label(root, text="Seed:")
        self.seed_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=20)
        self.seed_entry = tk.Entry(root, width=15, state='disabled')
        self.seed_entry.grid(row=3, column=0, sticky="w", padx=55)
        self.random_seed_var = tk.BooleanVar(value=True)
        self.random_seed_checkbutton = tk.Checkbutton(text="RANDOM", variable=self.random_seed_var, command=self.toggle_random_seed)
        self.random_seed_checkbutton.grid(row=3, column=0, sticky="e")

        self.root.grid_columnconfigure(2, minsize=20)

        self.style_var = tk.StringVar(value=self.default_styles[0])
        self.style_combobox = ttk.Combobox(root, textvariable=self.style_var, values=self.styles, state="readonly", width=17)
        self.style_combobox.grid(row=3, column=3, columnspan=3, sticky="w", padx=10)
        self.style_combobox.bind("<<ComboboxSelected>>", self.on_style_selected)

        self.wrap_treatment_frame = tk.Frame(root)
        self.wrap_treatment_frame.grid(row=4, column=0, columnspan=6, sticky="ew")
        tk.Label(self.wrap_treatment_frame, text="WRAP:").pack(side=tk.LEFT)
        self.wrap_treatment_combobox = ttk.Combobox(self.wrap_treatment_frame, values=["None"] + list(self.wrap_treatments.keys()), state="readonly")
        self.wrap_treatment_combobox.pack(side=tk.LEFT)
        self.wrap_treatment_combobox.set("None")
        tk.Button(self.wrap_treatment_frame, text="Add", command=self.add_wrap_treatment).pack(side=tk.LEFT)
        tk.Button(self.wrap_treatment_frame, text="Edit", command=self.edit_wrap_treatment).pack(side=tk.LEFT)
        tk.Button(self.wrap_treatment_frame, text="Rename", command=self.rename_wrap_treatment).pack(side=tk.LEFT)
        tk.Button(self.wrap_treatment_frame, text="Delete", command=self.delete_wrap_treatment).pack(side=tk.LEFT)

        self.ratio_var = tk.StringVar(value="1:1")
        self.ratio_1_1 = tk.Radiobutton(root, text="1:1", variable=self.ratio_var, value="1:1", command=self.toggle_ratio, padx=50)
        self.ratio_1_1.grid(row=5, column=0, sticky="w")
        self.ratio_3_4 = tk.Radiobutton(root, text="3:4", variable=self.ratio_var, value="3:4", command=self.toggle_ratio)
        self.ratio_3_4.grid(row=5, column=1, sticky="w")
        self.ratio_16_9 = tk.Radiobutton(root, text="16:9", variable=self.ratio_var, value="16:9", command=self.toggle_ratio)
        self.ratio_16_9.grid(row=5, column=2, sticky="w")
        self.ratio_custom = tk.Radiobutton(root, text="Custom", variable=self.ratio_var, value="Custom", command=self.toggle_ratio, padx=50)
        self.ratio_custom.grid(row=6, column=0, sticky="w")
        self.custom_width_label = tk.Label(root, text="W:")
        self.custom_width_label.grid(row=6, column=1, sticky="w")
        self.custom_width_entry = tk.Entry(root, width=5)
        self.custom_width_entry.grid(row=6, column=1, sticky="w", padx=25)
        self.custom_height_label = tk.Label(root, text="H:")
        self.custom_height_label.grid(row=6, column=2, sticky="w")
        self.custom_height_entry = tk.Entry(root, width=5)
        self.custom_height_entry.grid(row=6, column=2, sticky="w", padx=25)
        self.toggle_ratio()

        self.timer_frame = tk.Frame(root)
        self.timer_frame.grid(row=7, column=0, columnspan=6, sticky="ew")
        self.enable_timer_var = tk.BooleanVar(value=False)
        self.enable_timer_checkbutton = tk.Checkbutton(self.timer_frame, text="Enable Timer", variable=self.enable_timer_var)
        self.enable_timer_checkbutton.grid(row=0, column=0, sticky="w", padx=5)
        self.retries_label = tk.Label(self.timer_frame, text="Retries:")
        self.retries_label.grid(row=0, column=1, sticky="w", padx=5)
        self.retries_entry = tk.Entry(self.timer_frame, width=5)
        self.retries_entry.grid(row=0, column=2, sticky="w")
        self.delay_label = tk.Label(self.timer_frame, text="Delay (s):")
        self.delay_label.grid(row=0, column=3, sticky="w", padx=5)
        self.delay_entry = tk.Entry(self.timer_frame, width=5)
        self.delay_entry.grid(row=0, column=4, sticky="w")

        self.folder_button = tk.Button(root, text="📁 Images", command=self.open_save_path, width=9)
        self.folder_button.grid(row=8, column=0, sticky="w", padx=10)
        self.generate_button = tk.Button(root, text="GENERATE", command=self.on_generate_button_click)
        self.generate_button.grid(row=8, column=0, columnspan=4, sticky="ew", padx=140)
        self.custom_style_button = tk.Button(root, text="EDIT STYLES", command=self.open_custom_styles_editor)
        self.custom_style_button.grid(row=5, column=3, sticky="ew", padx=10)

        self.canvas = tk.Canvas(root, bg="white", width=512, height=512)
        self.canvas.grid(row=9, column=0, columnspan=6)

        self.status_bar = tk.Label(root, text="", bg="lightgrey", height=1)
        self.status_bar.grid(row=10, column=0, columnspan=6, sticky="ew")

        # Modify the thumbnail frame setup
        self.thumbnail_frame = tk.Frame(root, height=100)  # Increased height to accommodate scrollbar
        self.thumbnail_frame.grid(row=10, column=0, columnspan=6, sticky="ew")
        self.thumbnail_frame.grid_propagate(False)

        self.thumbnail_canvas = tk.Canvas(self.thumbnail_frame, height=80)
        self.thumbnail_canvas.pack(side=tk.TOP, fill=tk.X, expand=True)

        self.thumbnail_scrollbar = tk.Scrollbar(self.thumbnail_frame, orient=tk.HORIZONTAL, command=self.thumbnail_canvas.xview)
        self.thumbnail_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.thumbnail_canvas.configure(xscrollcommand=self.thumbnail_scrollbar.set)
        
        self.thumbnail_inner_frame = tk.Frame(self.thumbnail_canvas)
        self.thumbnail_canvas.create_window((0, 0), window=self.thumbnail_inner_frame, anchor="nw")
        
        self.thumbnail_inner_frame.bind("<Configure>", self.on_thumbnail_frame_configure)
        self.thumbnail_canvas.bind("<Configure>", self.on_thumbnail_canvas_configure)

        self.load_settings()

        self.root.update_idletasks()
        self.root.after_idle(self.prevent_resize)

        self.update_wrap_treatment_combobox()
        print("Initialization complete.")
        
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.loop.run_forever)
        self.loop_thread.start()

        self.load_existing_images()


    def prevent_resize(self):
        # Set a minimum and maximum width for the window
        self.root.minsize(520, 880)  # You can adjust these values to fit your layout
        self.root.maxsize(800, 1000)  # Adjust the maximum size to avoid sliding behavior


    def on_frame_configure(self, event):
        self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))
        self.thumbnail_canvas.config(width=self.thumbnail_frame.winfo_width())

    def on_style_selected(self, event):
        selected_style = self.style_var.get()

    def toggle_always_on_top(self):
        print("Toggling always on top...")
        self.root.attributes("-topmost", self.always_on_top_var.get())
        print(f"Always on top set to: {self.always_on_top_var.get()}")

    def toggle_random_seed(self):
        if self.random_seed_var.get():
            self.seed_entry.config(state='disabled')
        else:
            self.seed_entry.config(state='normal')

    def toggle_ratio(self):
        if self.ratio_var.get() == "Custom":
            self.custom_width_entry.config(state='normal')
            self.custom_height_entry.config(state='normal')
        else:
            self.custom_width_entry.config(state='disabled')
            self.custom_height_entry.config(state='disabled')

    def load_user_styles(self):
        print("Loading user styles...")
        user_styles = []
        user_styles_file = './ASSETS/user_styles.txt'
        if os.path.exists(user_styles_file):
            with open(user_styles_file, "r", encoding='utf-8') as file:
                user_styles = [line.strip() for line in file.readlines() if not line.strip().startswith("#")]
        print(f"Loaded user styles: {user_styles}")
        return user_styles

    def load_styles_from_file(self):
        print("Loading styles from file...")
        styles = []
        styles_file = './ASSETS/styles.txt'
        if os.path.exists(styles_file):
            with open(styles_file, "r", encoding='utf-8') as file:
                styles = [line.strip() for line in file.readlines() if not line.strip().startswith("#")]
        print(f"Loaded styles: {styles}")
        return styles

    def save_user_styles(self):
        print("Saving user styles...")
        user_styles_file = './ASSETS/user_styles.txt'
        with open(user_styles_file, "w", encoding='utf-8') as file:
            for style in self.user_styles:
                if not style.startswith("#"):
                    file.write(style + "\n")
        print("User styles saved.")

    def open_custom_styles_editor(self):
        self.current_style_before_edit = self.style_var.get()
        editor_window = tk.Toplevel(self.root)
        editor_window.title("Custom Styles Editor")
        editor_window.geometry("600x430")
        editor_window.attributes("-topmost", True)
        text_widget = tk.Text(editor_window)
        text_widget.pack(fill=tk.BOTH, expand=True)

        user_styles_file = './ASSETS/user_styles.txt'
        try:
            with open(user_styles_file, "r", encoding='utf-8') as file:
                styles_content = file.read()
        except FileNotFoundError:
            styles_content = ""

        example_format = "# Example format:\n# Style Name: (positive1, positive2, positive3, etc), (negative1, negative2, etc)\n\n"
        text_widget.insert(tk.END, example_format + styles_content)

        def save_styles():
            new_styles_content = text_widget.get("1.0", tk.END)
            with open(user_styles_file, "w", encoding='utf-8') as file:
                file.write(new_styles_content.strip())
            self.user_styles = [line.strip() for line in new_styles_content.strip().split("\n") if not line.strip().startswith("#") and line.strip()]
            self.save_user_styles()
            self.update_style_button()
            editor_window.destroy()

        def on_editor_close():
            self.style_var.set(self.current_style_before_edit)
            editor_window.destroy()

        save_button = tk.Button(editor_window, text="Save Styles", command=save_styles)
        save_button.pack(side=tk.BOTTOM, padx=10, pady=10)

        editor_window.protocol("WM_DELETE_WINDOW", on_editor_close)

    def update_style_button(self):
        self.styles = self.default_styles + [style.split(":", 1)[0] for style in self.user_styles]
        self.style_var.set(self.styles[0])
        self.style_combobox['values'] = self.styles

    def set_save_path(self):
        new_path = filedialog.askdirectory()
        if new_path:
            self.save_path = new_path
            self.status_bar.config(text=f"Save path set to: {self.save_path}")

    def set_backup_path(self):
        new_path = filedialog.askdirectory()
        if new_path:
            self.backup_path = new_path
            self.save_settings()
            self.wrap_treatments = self.load_wrap_treatments()
            self.update_wrap_treatment_combobox()
            self.status_bar.config(text=f"Backup path set to: {self.backup_path}")

    async def async_generate_image(self, url):
        print(f"Starting async image generation for URL: {urllib.parse.unquote(url)}")
        retries = 3
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        response.raise_for_status()
                        content = await response.read()
                        print(f"Image fetched successfully from URL: {urllib.parse.unquote(url)}")
                        return Image.open(io.BytesIO(content))
            except aiohttp.ClientError as e:
                print(f"Attempt {attempt + 1} failed for URL: {url} with error: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    print(f"Failed to retrieve image from {url}. Error: {e}")
                    return None

    async def generate_images_async(self, urls):
        print(f"Generating images async for URLs: {urls}")
        tasks = [self.async_generate_image(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def generate_image(self):
        if self.generating_image:
            return

        self.generating_image = True
        print("Generate image button clicked.")
        self.status_bar.config(text="IN QUEUE, WAITING FOR IMAGE...")
        prompt = self.prompt_entry.get()
        print(f"Prompt entered: {prompt}")
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt")
            self.status_bar.config(text="")
            self.generating_image = False
            return

        self.update_prompt_history(prompt)

        style = self.style_var.get()
        print(f"User selected style: {style}")
        if style == "Empty":
            full_prompt = prompt
        elif style in [s.split(":", 1)[0] for s in self.user_styles]:
            style_index = [s.split(":", 1)[0] for s in self.user_styles].index(style)
            style_components = self.user_styles[style_index].split(":", 1)[1].split("),")
            style_traits = style_components[0].strip("()").strip()
            full_prompt = f"{prompt}, {style_traits}, {style} style".strip()
            negative_style = style_components[1].strip("() ").strip() if len(style_components) > 1 else ""
        else:
            messagebox.showerror("Error", "Selected style is not valid")
            self.status_bar.config(text="")
            self.generating_image = False
            return

        selected_wrap = self.wrap_treatment_combobox.get()
        if selected_wrap != "None":
            wrap = self.wrap_treatments[selected_wrap]
            full_prompt = f"{wrap['pre']} {full_prompt} {wrap['post']}".strip()

        nologo_password = self.nologo_password_entry.get()
        if nologo_password:
            nologo_param = f"nologo={nologo_password}"
        else:
            nologo_param = "nologo=true"

        params = [nologo_param]
        if self.private_var.get():
            params.append("nofeed=true")

        if self.random_seed_var.get():
            seed = str(random.randint(0, 99999))
            self.status_bar.config(text=f"Random Seed: {seed}")
        else:
            seed = self.seed_entry.get()
            self.status_bar.config(text=f"Seed: {seed}")
        params.append(f"seed={seed}")

        if self.ratio_var.get() == "1:1":
            width, height = "1024", "1024"
        elif self.ratio_var.get() == "3:4":
            width, height = "768", "1024"
        elif self.ratio_var.get() == "16:9":
            width, height = "1024", "576"
        else:
            width = self.custom_width_entry.get()
            height = self.custom_height_entry.get()
        params.append(f"width={width}")
        params.append(f"height={height}")
        params.append(f"enhance={str(self.enhance_var.get()).lower()}")

        full_prompt_no_parentheses = full_prompt.replace("(", "").replace(")", "").strip()
        encoded_prompt = urllib.parse.quote(full_prompt_no_parentheses)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{'&'.join(params)}"

        if self.use_negative_var.get() and negative_style:
            negative_style_no_parentheses = negative_style.replace("(", "").replace(")", "").strip()
            encoded_negative = urllib.parse.quote(negative_style_no_parentheses)
            url += f"&negative={encoded_negative}"

        decoded_url = urllib.parse.unquote(url)
        print(f"Sending request to URL: {decoded_url}")

        try:
            images = await self.generate_images_async([url])
            images = [img for img in images if img is not None]
            if images:
                print(f"Image received")
                self.image = images[0]
                self.display_image(self.image)
                self.save_image(self.image)
                self.update_thumbnails(self.image)
            else:
                messagebox.showerror("Error", "Failed to retrieve image after multiple attempts.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve image. Error: {e}")
        finally:
            self.status_bar.config(text="Image generation complete.")
            print("Status bar reset.")
            self.generating_image = False

    async def async_generate_image(self, url):
        print(f"Starting async image generation for URL: {urllib.parse.unquote(url)}")
        retries = 3
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        response.raise_for_status()
                        content = await response.read()
                        print(f"Image fetched successfully from URL: {urllib.parse.unquote(url)}")
                        return Image.open(io.BytesIO(content))
            except aiohttp.ClientError as e:
                print(f"Attempt {attempt + 1} failed for URL: {url} with error: {e}")
                if attempt < retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    print(f"Failed to retrieve image from {url}. Error: {e}")
                    return None


    def display_image(self, image):
        if image is None:
            print("Resize error: image is None.")
            return
        print("Displaying image...")
        self.canvas.delete("all")
        self.image_to_copy = image
        
        canvas_width, canvas_height = self.calculate_display_size(image)
        
        display_image_resized = self.resize_proportionally(image, canvas_width, canvas_height)
        self.tk_images = [ImageTk.PhotoImage(display_image_resized)]
        
        x_center = canvas_width // 2
        y_center = canvas_height // 2
        self.canvas.create_image(
            x_center, y_center, anchor=tk.CENTER, image=self.tk_images[-1],
            tags="image"
        )
        self.canvas.tag_bind("image", "<Button-1>", lambda e: self.enlarge_image(image=image))
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.adjust_canvas_size(canvas_width, canvas_height)
        print("Image displayed.")

    def adjust_canvas_size(self, canvas_width, canvas_height):
        min_gui_width = 520
        gui_width = max(canvas_width + 8, min_gui_width)
        
        gui_elements_height = 336
        
        self.canvas.config(width=canvas_width, height=canvas_height)
        
        self.root.geometry(f"{gui_width}x{canvas_height + gui_elements_height}")

    def calculate_display_size(self, image, max_width=512, max_height=512):
        width, height = image.size
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        return new_width, new_height

    def resize_image(self, event):
        print("Resizing image...")
        if self.image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            resized_image = self.resize_proportionally(self.image, canvas_width, canvas_height)
            if resized_image:
                self.tk_images[0] = ImageTk.PhotoImage(resized_image)
                self.canvas.coords(self.canvas.find_withtag("image"), 0, 0)
                self.canvas.itemconfig(self.canvas.find_withtag("image"), image=self.tk_images[0])
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        print("Image resizing complete.")

    def resize_proportionally(self, image, max_width, max_height):
        if image is None:
            print("Resize error: image is None.")
            return None
        if isinstance(image, ImageTk.PhotoImage):
            print("ImageTk.PhotoImage instance found. Skipping resize.")
            return image
        image_width, image_height = image.size
        ratio = min(max_width / image_width, max_height / image_height)
        new_width = int(image_width * ratio)
        new_height = int(image_height * ratio)
        return image.resize((new_width, new_height), Image.LANCZOS)

    def save_image(self, image):
        print("Saving image...")
        if not os.path.exists(self.save_path):
            os.makedirs(self.save_path)
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_id = random.randint(1000, 9999)
        save_path = os.path.join(self.save_path, f"Image-{timestamp}-{unique_id}.png")
        image.save(save_path, "PNG")
        self.saved_image_path = save_path
        print(f"Image saved to: {self.saved_image_path}")

    def copy_to_clipboard(self):
        print("Copying image to clipboard...")
        if hasattr(self, 'image_to_copy') and self.image_to_copy:
            output = io.BytesIO()
            self.image_to_copy.convert("RGB").save(output, format="BMP")
            data = output.getvalue()[14:]
            output.close()
            try:
                import win32clipboard
                win32clipboard.OpenClipboard()
                win32clipboard.EmptyClipboard()
                win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                win32clipboard.CloseClipboard()
                print("Image copied to clipboard.")
            except ImportError:
                messagebox.showerror("Error", "Failed to import win32clipboard module.")
                print("Error: Failed to import win32clipboard module.")
        else:
            messagebox.showerror("Error", "No image to copy. Generate an image first.")
            print("Error: No image to copy.")

    def calculate_enlarged_size(self, image, max_width=800, max_height=800):
        width, height = image.size
        scale = min(max_width / width, max_height / height)
        new_width = int(width * scale)
        new_height = int(height * scale)
        return new_width, new_height

    def enlarge_image(self, event=None, image=None):
        if image is None:
            image = self.image
        if image is None:
            print("No image to enlarge.")
            return
        if hasattr(self, 'enlarged_window') and self.enlarged_window.winfo_exists():
            self.enlarged_window.lift()
            return
        
        print("Enlarging image...")
        self.enlarged_window = tk.Toplevel(self.root)
        self.enlarged_window.title("Enlarged Image")
        
        enlarged_width, enlarged_height = self.calculate_enlarged_size(image)
        
        self.enlarged_window.geometry(f"{enlarged_width}x{enlarged_height}")
        self.enlarged_window.attributes("-topmost", True)
        
        img_resized = image.resize((enlarged_width, enlarged_height), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_resized)
        
        canvas = tk.Canvas(self.enlarged_window, width=enlarged_width, height=enlarged_height)
        canvas.pack(fill=tk.BOTH, expand=True)
        
        canvas.create_image(enlarged_width//2, enlarged_height//2, anchor=tk.CENTER, image=img_tk)
        canvas.image = img_tk

    def load_settings(self):
        print("Loading settings...")
        if os.path.exists("settings.txt"):
            with open("settings.txt", "r", encoding='utf-8') as file:
                settings = file.read().splitlines()
                if settings:
                    self.nologo_password_entry.insert(0, settings[0] if len(settings) > 0 else "")
                    self.private_var.set(settings[1] == 'True' if len(settings) > 1 else False)
                    self.seed_entry.insert(0, settings[2] if len(settings) > 2 else "")
                    self.style_var.set(settings[3] if len(settings) > 3 else self.default_styles[0])
                    self.enhance_var.set(settings[4] == 'True' if len(settings) > 4 else False)
                    self.ratio_var.set(settings[5] if len(settings) > 5 else "1:1")
                    if len(settings) > 6:
                        self.custom_width_entry.insert(0, settings[6])
                    if len(settings) > 7:
                        self.custom_height_entry.insert(0, settings[7])
                    if len(settings) > 8:
                        self.save_path = settings[8]
                    if len(settings) > 9:
                        self.enable_timer_var.set(settings[9] == 'True')
                    if len(settings) > 10:
                        self.retries_entry.insert(0, settings[10])
                    if len(settings) > 11:
                        self.delay_entry.insert(0, settings[11])
                    if len(settings) > 12:
                        self.use_negative_var.set(settings[12] == 'True')
                    if len(settings) > 13:
                        self.backup_path = settings[13]
                        print(f"Loaded backup path: {self.backup_path}")
        print("Settings loaded.")

    def save_settings(self):
        print("Saving settings...")
        with open("settings.txt", "w", encoding='utf-8') as file:
            file.write(f"{self.nologo_password_entry.get()}\n")
            file.write(f"{self.private_var.get()}\n")
            file.write(f"{self.seed_entry.get()}\n")
            file.write(f"{self.style_var.get()}\n")
            file.write(f"{self.enhance_var.get()}\n")
            file.write(f"{self.ratio_var.get()}\n")
            file.write(f"{self.custom_width_entry.get()}\n")
            file.write(f"{self.custom_height_entry.get()}\n")
            file.write(f"{self.save_path}\n")
            file.write(f"{self.enable_timer_var.get()}\n")
            file.write(f"{self.retries_entry.get()}\n")
            file.write(f"{self.delay_entry.get()}\n")
            file.write(f"{self.use_negative_var.get()}\n")
            file.write(f"{self.backup_path}\n")
        print("Settings saved.")

    def update_script(self):
        print("Checking for script updates...")
        repo_url = "https://api.github.com/repos/Tolerable/POLLI-GEN/contents/POLLI-GEN.py"
        headers = {"Accept": "application/vnd.github.v3+json"}
        try:
            response = requests.get(repo_url, headers=headers)
            response.raise_for_status()
            repo_data = response.json()
            remote_sha = repo_data['sha']
            remote_file_url = repo_data['download_url']
            with open(__file__, 'rb') as file:
                local_sha = hashlib.sha256(file.read()).hexdigest()
            if local_sha != remote_sha:
                self.status_bar.config(text="Updating script...")
                script_content = requests.get(remote_file_url).text
                backup_file = __file__ + ".backup"
                with open(backup_file, 'w', encoding='utf-8') as file:
                    file.write(open(__file__).read())
                with open(__file__, 'w', encoding='utf-8') as file:
                    file.write(script_content)
                self.status_bar.config(text="Script updated. Please restart the application.")
                print("Script updated. Please restart the application.")
            else:
                self.status_bar.config(text="No updates available.")
                print("No updates available.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update script. Error: {e}")
            self.status_bar.config(text="Update failed.")
            print(f"Failed to update script. Error: {e}")

    def on_closing(self):
        print("Closing application...")
        self.save_settings()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.loop_thread.join()
        self.root.destroy()
        print("Application closed.")

    def start_timer(self):
        if not self.timer_running:
            self.timer_running = True
            asyncio.run_coroutine_threadsafe(self.run_timer(), self.loop)

    def stop_timer(self):
        self.timer_running = False
        self.enable_timer_var.set(False)

    async def run_timer(self):
        if not self.timer_running:
            return
        try:
            retries = int(self.retries_entry.get())
            delay = int(self.delay_entry.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for retries and delay")
            self.stop_timer()
            return

        remaining_retries = retries

        while remaining_retries > 0 and self.timer_running:
            self.status_bar.config(text=f"Retries left: {remaining_retries - 1}")
            await self.generate_image()
            remaining_retries -= 1
            self.retries_entry.delete(0, tk.END)
            self.retries_entry.insert(0, str(remaining_retries))
            if remaining_retries > 0:
                await asyncio.sleep(delay)

        self.stop_timer()
        self.status_bar.config(text="Timer finished")
        self.enable_timer_var.set(False)

    def on_generate_button_click(self, event=None):
        print("Generate button clicked. Calling generate_image()...")
        self.status_bar.config(text="IN QUEUE, WAITING FOR IMAGE...")
        asyncio.run_coroutine_threadsafe(self.generate_image(), self.loop)
        if self.enable_timer_var.get() and not self.timer_running:
            self.start_timer()

    def open_save_path(self):
        print("Opened save path")
        path = os.path.abspath(self.save_path)
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Error", f"Save path does not exist: {path}")

    def show_about_dialog(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("About Polli-Gen Image Generator")
        about_window.geometry("500x380")
        about_window.resizable(False, False)
        about_window.attributes("-topmost", True)

        about_frame = tk.Frame(about_window, padx=10, pady=10)
        about_frame.pack(expand=True, fill=tk.BOTH)

        about_text = (
            "Polli-Gen Image Generator\n"
            f"Version {CURRENT_VERSION}\n\n"
            "This project uses the Pollinations service to generate images based on user prompts.\n"
            "It is not an official product of Pollinations.\n\n"
            "Original Author: Tolerable\n\n"
            "Contributors: Scruffynerf, uwoneko & Pollinations of course\n"
        )

        about_label = tk.Label(about_frame, text=about_text, justify=tk.LEFT, anchor="w")
        about_label.pack(anchor="w")

        def open_link(url):
            webbrowser.open_new_tab(url)

        links = [
            ("https://github.com/Tolerable/POLLI-GEN/", "POLLI-GEN by Tolerable"),
            ("https://github.com/scruffynerf/", "GitHub - Scruffynerf"),
            ("https://github.com/uwoneko/", "GitHub - uwoneko"),
            (None, ""),
            ("https://pollinations.ai/", "Pollinations Website"),
            ("https://discord.gg/8HqSRhJVxn", "Pollinations Discord")
        ]

        for url, text in links:
            if url is None:
                link = tk.Label(about_frame, text="", anchor="w")
            else:
                link = tk.Label(about_frame, text=text, fg="blue", cursor="hand2", anchor="w", padx=10)
                link.bind("<Button-1>", lambda e, url=url: open_link(url))
            link.pack(anchor="w")

        tk.Button(about_frame, text="Close", command=about_window.destroy).pack(pady=10, anchor="center")

    def load_existing_images(self):
        if not os.path.exists(self.save_path):
            return

        images = sorted(
            (os.path.join(self.save_path, f) for f in os.listdir(self.save_path) if f.endswith(".png")),
            key=os.path.getmtime,
            reverse=True
        )[:50]

        for image_path in images:
            image = Image.open(image_path)
            self.generated_images.append(image)

        self.update_thumbnails()
        if self.generated_images:
            self.display_image(self.generated_images[0])

    def on_thumbnail_frame_configure(self, event):
        self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))

    def on_thumbnail_canvas_configure(self, event):
        self.thumbnail_canvas.itemconfig(self.thumbnail_canvas.find_withtag("window")[0], width=event.width)

    def update_thumbnails(self, new_image=None):
        if new_image:
            self.generated_images.insert(0, new_image)

        for widget in self.thumbnail_inner_frame.winfo_children():
            widget.destroy()

        for img in self.generated_images[:25]:  # Limit to 25 thumbnails for performance
            thumbnail = self.resize_proportionally(img, 80, 80)
            tk_image = ImageTk.PhotoImage(thumbnail)
            label = tk.Label(self.thumbnail_inner_frame, image=tk_image)
            label.image = tk_image
            label.pack(side=tk.LEFT, padx=2)
            label.bind("<Button-1>", lambda e, img=img: self.display_image(img))

        self.thumbnail_inner_frame.update_idletasks()
        self.thumbnail_canvas.configure(scrollregion=self.thumbnail_canvas.bbox("all"))

    def load_wrap_treatments(self):
        try:
            if self.backup_path:
                file_path = os.path.join(self.backup_path, 'wrap_treatments.json')
            else:
                file_path = 'wrap_treatments.json'  # Ensure consistency with the correct file name
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def save_wrap_treatments(self):
        if self.backup_path:
            file_path = os.path.join(self.backup_path, 'wrap_treatments.json')  # Use the correct file name
        else:
            file_path = 'wrap_treatments.json'  # Use the correct file name
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.wrap_treatments, f, indent=2)

    def add_wrap_treatment(self):
        dialog = WrapTreatmentDialog(self.root)
        if dialog.result:
            name, pre, post = dialog.result
            self.wrap_treatments[name] = {"pre": pre, "post": post}
            self.save_wrap_treatments()
            self.update_wrap_treatment_combobox()

    def edit_wrap_treatment(self):
        selected = self.wrap_treatment_combobox.get()
        if selected != "None":
            treatment = self.wrap_treatments[selected]
            dialog = WrapTreatmentDialog(self.root, name=selected, pre=treatment['pre'], post=treatment['post'])
            if dialog.result:
                name, pre, post = dialog.result
                self.wrap_treatments[selected] = {"pre": pre, "post": post}
                self.save_wrap_treatments()

    def rename_wrap_treatment(self):
        current_name = self.wrap_treatment_combobox.get()
        if current_name != "None":
            new_name = simpledialog.askstring("Rename Treatment", "Enter new name:", initialvalue=current_name)
            if new_name:
                self.wrap_treatments[new_name] = self.wrap_treatments.pop(current_name)
                self.save_wrap_treatments()
                self.update_wrap_treatment_combobox()

    def delete_wrap_treatment(self):
        current_name = self.wrap_treatment_combobox.get()
        if current_name != "None":
            if messagebox.askyesno("Delete Treatment", f"Are you sure you want to delete '{current_name}'?"):
                del self.wrap_treatments[current_name]
                self.save_wrap_treatments()
                self.update_wrap_treatment_combobox()

    def update_wrap_treatment_combobox(self):
        current = self.wrap_treatment_combobox.get()
        self.wrap_treatment_combobox['values'] = ["None"] + list(self.wrap_treatments.keys())
        if current in self.wrap_treatments or current == "None":
            self.wrap_treatment_combobox.set(current)
        else:
            self.wrap_treatment_combobox.set("None")

    def load_prompt_history(self):
        try:
            with open('prompt_history.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def save_prompt_history(self):
        with open('prompt_history.json', 'w') as f:
            json.dump(self.prompt_history, f)

    def update_prompt_history(self, prompt):
        if prompt not in self.prompt_history:
            self.prompt_history.insert(0, prompt)
            self.prompt_history = self.prompt_history[:10]  # Keep only the last 10 prompts
            self.save_prompt_history()
            self.prompt_history_combobox['values'] = self.prompt_history

    def load_prompt_from_history(self, event):
        selected_prompt = self.prompt_history_combobox.get()
        self.prompt_entry.delete(0, tk.END)
        self.prompt_entry.insert(0, selected_prompt)

    def on_entry_click(self, event):
        if self.prompt_entry.get() == "Enter your prompt and click 'GENERATE'":
            self.prompt_entry.delete(0, tk.END)
            self.prompt_entry.config(fg='black')

    def on_focusout(self, event):
        if self.prompt_entry.get() == '':
            self.prompt_entry.insert(0, "Enter your prompt and click 'GENERATE'")
            self.prompt_entry.config(fg='grey')

    def show_context_menu(self, event):
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="Copy", command=self.copy_to_clipboard)
        context_menu.post(event.x_root, event.y_root)

if __name__ == "__main__":
    print("Starting application...")
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()
    print("Application started.")