import tkinter as tk
from tkinter import messagebox, filedialog
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

# Define the current version of the script
CURRENT_VERSION = "1.2.116"

class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pollinations Image Generator")
        self.root.attributes("-topmost", True)
        self.root.geometry("520x640")
        self.root.resizable(False, False)

        self.save_path = os.path.abspath('./GENERATED')
        self.timer_running = False
        self.generating_image = False

        self.default_styles = ["Empty"]
        self.user_styles = self.load_styles_from_file()
        self.styles = self.default_styles + [style.split(":")[0] for style in self.user_styles]

        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        self.options_menu.add_command(label="Set Save Path", command=self.set_save_path)
        self.options_menu.add_command(label="Update Script", command=self.update_script)
        self.options_menu.add_separator()
        self.options_menu.add_command(label="About", command=self.show_about_dialog)

        self.nologo_password_label = tk.Label(self.options_menu, text="No Logo Password (optional):")
        self.nologo_password_label.pack()
        self.nologo_password_entry = tk.Entry(self.options_menu)
        self.nologo_password_entry.pack()
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.options_menu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.always_on_top_var, command=self.toggle_always_on_top)

        self.label = tk.Label(root, text="Enter your prompt and click 'GENERATE':")
        self.label.grid(row=0, column=0, columnspan=6, sticky="ew")
        self.prompt_entry = tk.Entry(root, justify='center')
        self.prompt_entry.grid(row=1, column=0, columnspan=6, sticky="ew")
        self.prompt_entry.bind("<Return>", self.on_generate_button_click)

        self.enhance_var = tk.BooleanVar(value=False)
        self.enhance_checkbutton = tk.Checkbutton(root, text="Enhance Image", variable=self.enhance_var)
        self.enhance_checkbutton.grid(row=2, column=0, columnspan=2, sticky="we")
        self.private_var = tk.BooleanVar(value=True)
        self.private_checkbutton = tk.Checkbutton(root, text="Private", variable=self.private_var)
        self.private_checkbutton.grid(row=2, column=2, columnspan=2, sticky="we")

        self.seed_label = tk.Label(root, text="Seed:")
        self.seed_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=20)
        self.seed_entry = tk.Entry(root, width=15)
        self.seed_entry.grid(row=3, column=0, sticky="w", padx=55)
        self.random_seed_var = tk.BooleanVar(value=True)
        self.random_seed_checkbutton = tk.Checkbutton(text="RANDOM", variable=self.random_seed_var, command=self.toggle_random_seed)
        self.random_seed_checkbutton.grid(row=3, column=0, sticky="e")
        self.style_var = tk.StringVar(value=self.default_styles[0])
        self.style_menu = tk.OptionMenu(root, self.style_var, *self.styles)
        self.style_menu.grid(row=3, column=3, columnspan=3, sticky="w", padx=10)

        self.ratio_var = tk.StringVar(value="1:1")
        self.ratio_1_1 = tk.Radiobutton(root, text="1:1", variable=self.ratio_var, value="1:1", command=self.toggle_ratio, padx=50)
        self.ratio_1_1.grid(row=4, column=0, sticky="w")
        self.ratio_3_4 = tk.Radiobutton(root, text="3:4", variable=self.ratio_var, value="3:4", command=self.toggle_ratio)
        self.ratio_3_4.grid(row=4, column=1, sticky="w")
        self.ratio_16_9 = tk.Radiobutton(root, text="16:9", variable=self.ratio_var, value="16:9", command=self.toggle_ratio)
        self.ratio_16_9.grid(row=4, column=2, sticky="w")
        self.ratio_custom = tk.Radiobutton(root, text="Custom", variable=self.ratio_var, value="Custom", command=self.toggle_ratio, padx=50)
        self.ratio_custom.grid(row=5, column=0, sticky="w")
        self.custom_width_label = tk.Label(root, text="W:")
        self.custom_width_label.grid(row=5, column=1, sticky="w")
        self.custom_width_entry = tk.Entry(root, width=5)
        self.custom_width_entry.grid(row=5, column=1, sticky="w", padx=25)
        self.custom_height_label = tk.Label(root, text="H:")
        self.custom_height_label.grid(row=5, column=2, sticky="w")
        self.custom_height_entry = tk.Entry(root, width=5)
        self.custom_height_entry.grid(row=5, column=2, sticky="w", padx=25)
        self.toggle_ratio()

        self.timer_frame = tk.Frame(root)
        self.timer_frame.grid(row=6, column=0, columnspan=6, sticky="ew")
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
        self.folder_button.grid(row=7, column=0, sticky="w", padx=10)
        self.generate_button = tk.Button(root, text="GENERATE", command=self.on_generate_button_click)
        self.generate_button.grid(row=7, column=0, columnspan=4, sticky="ew", padx=140)
        self.custom_style_button = tk.Button(root, text="EDIT: USER STYLES", command=self.open_custom_styles_editor)
        self.custom_style_button.grid(row=4, column=3, sticky="ew", padx=10)
        self.copy_button = tk.Button(root, text="COPY", command=self.copy_to_clipboard)
        self.copy_button.grid(row=6, column=3, sticky="ew", padx=10)

        self.canvas = tk.Canvas(root, bg="white", width=512, height=512)
        self.canvas.grid(row=8, column=0, columnspan=6)

        self.status_bar = tk.Label(root, text="", bg="lightgrey", height=1)
        self.status_bar.grid(row=9, column=0, columnspan=6, sticky="ew")

        self.root.grid_rowconfigure(8, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)
        self.root.grid_columnconfigure(4, weight=1)
        self.root.grid_columnconfigure(5, weight=1)

        self.previous_width = self.root.winfo_width()
        self.previous_height = self.root.winfo_height()
        self.root.update_idletasks()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.load_settings()
        print("Initialization complete.")
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.loop.run_forever)
        self.loop_thread.start()

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
        if os.path.exists("user_styles.txt"):
            with open("user_styles.txt", "r", encoding='utf-8') as file:
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
        with open("user_styles.txt", "w", encoding='utf-8') as file:
            for style in self.user_styles:
                if not style.startswith("#"):
                    file.write(style + "\n")
        print("User styles saved.")

    def open_custom_styles_editor(self):
        editor_window = tk.Toplevel(self.root)
        editor_window.title("Custom Styles Editor")
        editor_window.geometry("600x430")
        editor_window.attributes("-topmost", True)
        text_widget = tk.Text(editor_window)
        text_widget.pack(fill=tk.BOTH, expand=True)

        try:
            with open("user_styles.txt", "r", encoding='utf-8') as file:
                styles_content = file.read()
        except FileNotFoundError:
            styles_content = ""

        example_format = "# Example format:\n# Style Name: (positive1, positive2, positive3, etc), (negative1, negative2, etc)\n\n"
        text_widget.insert(tk.END, example_format + styles_content)

        def save_styles():
            new_styles_content = text_widget.get("1.0", tk.END)
            with open("user_styles.txt", "w", encoding='utf-8') as file:
                file.write(new_styles_content.strip())
            self.user_styles = [line.strip() for line in new_styles_content.strip().split("\n") if not line.strip().startswith("#") and line.strip()]
            self.save_user_styles()
            self.update_style_menu()
            editor_window.destroy()

        save_button = tk.Button(editor_window, text="Save Styles", command=save_styles)
        save_button.pack(side=tk.BOTTOM, padx=10, pady=10)

        editor_window.protocol("WM_DELETE_WINDOW", save_styles)

    def update_style_menu(self):
        self.style_menu['menu'].delete(0, 'end')
        all_styles = self.default_styles + [style.split(":")[0] for style in self.user_styles]
        for style in all_styles:
            self.style_menu['menu'].add_command(label=style, command=tk._setit(self.style_var, style))
        self.style_var.set(all_styles[0])

    def set_save_path(self):
        new_path = filedialog.askdirectory()
        if new_path:
            self.save_path = new_path
            self.status_bar.config(text=f"Save path set to: {self.save_path}")

    async def async_generate_image(self, url):
        print(f"Starting async image generation for URL: {url}")
        retries = 3
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        response.raise_for_status()
                        content = await response.read()
                        print(f"Image fetched successfully from URL: {url}")
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

        style = self.style_var.get()
        print(f"User selected style: {style}")
        if style == "Empty":
            full_prompt = prompt
        elif style in [s.split(":")[0] for s in self.user_styles]:
            style_prompt = self.user_styles[[s.split(":")[0] for s in self.user_styles].index(style)].split(":")[1].split("),")[0] + "), {prompt}"
            full_prompt = style_prompt.format(prompt=prompt)
        else:
            messagebox.showerror("Error", "Selected style is not valid")
            self.status_bar.config(text="")
            self.generating_image = False
            return

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

        # URL encode the full prompt
        encoded_prompt = urllib.parse.quote(full_prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{'&'.join(params)}"
        print(f"Sending request to URL: {url}")

        try:
            images = await self.generate_images_async([url])
            images = [img for img in images if img is not None]
            if images:
                print(f"Image received")
                self.image = images[0]
                self.display_image(self.image)
                self.save_image(self.image)
            else:
                messagebox.showerror("Error", "Failed to retrieve image after multiple attempts.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve image. Error: {e}")
        finally:
            self.status_bar.config(text="Image generation complete.")
            print("Status bar reset.")
            self.generating_image = False

    def display_image(self, image):
        print("Displaying image...")
        self.canvas.delete("all")
        self.tk_images = []
        display_image_resized = self.resize_proportionally(image, 512, 512)
        self.tk_images.append(ImageTk.PhotoImage(display_image_resized))
        self.canvas.create_image(
            0, 0, anchor=tk.NW, image=self.tk_images[-1],
            tags="image"
        )
        self.canvas.tag_bind("image", "<Button-1>", self.enlarge_image)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        self.adjust_canvas_size(display_image_resized)
        print("Image displayed.")

    def adjust_canvas_size(self, image):
        canvas_width, canvas_height = image.size
        self.canvas.config(width=canvas_width, height=canvas_height)
        self.root.geometry(f"{canvas_width+8}x{canvas_height+256}")  # Adjusting for the GUI elements size

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
        if self.saved_image_path:
            image = Image.open(self.saved_image_path)
            output = io.BytesIO()
            image.convert("RGB").save(output, "BMP")
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

    def enlarge_image(self, event=None):
        if hasattr(self, 'enlarged_window') and self.enlarged_window.winfo_exists():
            self.enlarged_window.lift()
            return
        print("Enlarging image...")
        self.enlarged_window = tk.Toplevel(self.root)
        self.enlarged_window.title("Enlarged Image")
        self.enlarged_window.geometry("800x800")
        self.enlarged_window.attributes("-topmost", True)
        img_resized = self.image.resize((800, 800), Image.LANCZOS)
        img_tk = ImageTk.PhotoImage(img_resized)
        label = tk.Label(self.enlarged_window, image=img_tk)
        label.image = img_tk
        label.pack()

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
        while retries > 0 and self.timer_running:
            self.status_bar.config(text=f"Retries left: {retries - 1}")
            await self.generate_image()
            await asyncio.sleep(delay)
            retries -= 1
            self.retries_entry.delete(0, tk.END)
            self.retries_entry.insert(0, str(retries))
        if retries == 0:
            self.stop_timer()
            self.status_bar.config(text="Timer finished")

    def on_generate_button_click(self, event=None):
        print("Generate button clicked. Calling generate_image()...")
        self.status_bar.config(text="IN QUEUE, WAITING FOR IMAGE...")
        asyncio.run_coroutine_threadsafe(self.generate_image(), self.loop)
        if self.enable_timer_var.get() and not self.timer_running:
            self.start_timer()

    def open_save_path(self):
        path = os.path.abspath(self.save_path)
        if os.path.exists(path):
            os.startfile(path)
        else:
            messagebox.showerror("Error", f"Save path does not exist: {path}")

    def show_about_dialog(self):
        about_text = (
            "Pollinations Image Generator\n"
            f"Version {CURRENT_VERSION}\n\n"
            "This project uses the Pollinations service to generate images based on user prompts.\n"
            "It is not an official product of Pollinations.\n\n"
            "Contributors:\n"
            " - Tolerable: https://github.com/Tolerable/POLLI-GEN/\n"
            " - Scruffynerf: https://github.com/scruffynerf/\n\n"
            "Pollinations:\n"
            " - Website: https://pollinations.ai/\n"
            " - Discord: https://discord.gg/8HqSRhJVxn"
        )
        messagebox.showinfo("About", about_text)

if __name__ == "__main__":
    print("Starting application...")
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()
    print("Application started.")
