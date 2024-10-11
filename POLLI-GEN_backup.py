import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import Image, ImageTk
import requests
import io
import os
import datetime
import random
import asyncio
import aiohttp

# Define style keywords and their corresponding tags
style_tags = {
    "Anime": ("(anime:1.3), line drawing, asian influence, vibrant colors, cel shading, large expressive eyes, detailed hair, dynamic poses, action scenes, {prompt}", "realistic, deformed, noisy, blurry, stock photo"),
    "Op art": ("(op art), {prompt}, optical illusions, geometric, black and white, detailed", "no illusions, organic, colorful, low detail"),
    "Caricature": ("big head, big eyes, caricature, a caricature, digital rendering, (figurativism:0.8), {prompt}", "realistic, deformed, ugly, noisy"),
    "Cartoon-2D": ("2D, 2-d, line drawing, cartoon, flat, vibrant, drawn, animation, illustration, exaggerated features, expressive poses, whimsical, dynamic motion, humorous, {prompt}, colorful, lively, imaginative, stylized, caricatured, energetic, playful, surreal, fantastical, animated, expressive, fluid, bold outlines, clear shapes, simple forms, iconic, classic", "photorealistic, hyperrealistic, 3d, photo, photographic"),
    "Paper-cut": ("(paper-cut craft:1.2), {prompt}, amazing body, detailed", "noisy, messy, blurry, realistic"),
    "Render": ("epic realistic, hyperdetailed, (cycles render:1.3), caustics, (glossy:0.58), (artstation:0.82), {prompt}", "ugly, deformed, noisy, low poly, blurry, painting"),
    "3d Movie": ("epic realistic, pixar style, disney, (cycles render:1.3), caustics, (glossy:0.58), (artstation:0.2), cute, {prompt}", "sloppy, messy, grainy, highly detailed, ultra textured, photo"),
    "Engraving": ("(grayscale, woodcut:1.2), (etching:1.1), (engraving:0.2), {prompt}, detailed", "colored, blurry, noisy, soft, deformed"),
    "Comic book": ("neutral palette, comic style, muted colors, illustration, cartoon, soothing tones, low saturation, {prompt}", "realistic, photorealistic, blurry, noisy"),
    "Cinematic": ("(cinematic look:1.4), soothing tones, insane details, intricate details, hyperdetailed, low contrast, soft cinematic light, dim colors, exposure blend, hdr, faded, slate gray atmosphere, {prompt}", "grayscale, black and white, monochrome"),
    "Cinematic Horror": ("slate atmosphere, cinematic, dimmed colors, dark shot, muted colors, film grainy, lut, spooky, {prompt}", "anime, cartoon, graphic, text, painting, crayon, graphite, abstract, glitch, deformed, mutated, ugly, disfigured"),
    "Gloomy": ("complex background, stuff in the background, highly detailed, (gloomy:1.3), dark, dimmed, hdr, vignette, grimy, (slate atmosphere:0.8), {prompt}", "depth of field, bokeh, blur, blurred, pink"),
    "Professional photo": ("(dark shot:1.4), 80mm, {prompt}, soft light, sharp, exposure blend, medium shot, bokeh, (hdr:1.4), high contrast, (cinematic, teal and orange:0.85), (muted colors, dim colors, soothing tones:1.3), low saturation, (hyperdetailed:1.2), (noir:0.4)", "neon, over saturated"),
    "Painting": ("(oil painting:1.2), canvas texture, brush strokes, {prompt}, vivid colors, realistic, hyperdetailed", "deformed, noisy, blurry, distorted, grainy"),
    "Painting Vivid": ("(pascal campion:0.38), vivid colors, (painting art:0.06), [eclectic:clear:17], {prompt}", "vignette, cinematic, grayscale, bokeh, blurred, depth of field"),
    "Midjourney Warm": ("epic realistic, {prompt}, faded, (neutral colors:1.2), art, (hdr:1.5), (muted colors:1.1), (pastel:0.2), hyperdetailed, (artstation:1.4), warm lights, dramatic light, (intricate details:1.2), vignette, complex background, rutkowski", "ugly, deformed, noisy, blurry, distorted, grainy"),
    "Midjourney": ("(dark shot:1.1), epic realistic, {prompt}, faded, (neutral colors:1.2), (hdr:1.4), (muted colors:1.2), hyperdetailed, (artstation:1.4), cinematic, warm lights, dramatic light, (intricate details:1.1), complex background, (rutkowski:0.66), (teal and orange:0.4)", "ugly, deformed, noisy, blurry, distorted, grainy"),
    "XpucT": ("epic realistic, {prompt}, (dark shot:1.22), neutral colors, (hdr:1.4), (muted colors:1.4), (intricate), (artstation:1.2), hyperdetailed, dramatic, intricate details, (technicolor:0.9), (rutkowski:0.8), cinematic, detailed", "ugly, deformed, noisy, blurry, distorted, grainy"),
    "+ Details": ("(intricate details:1.12), hdr, (intricate details, hyperdetailed:1.15), {prompt}", "ugly, deformed, noisy, blurry"),
    "Neutral Background": ("(neutral background), {prompt}", "ugly, deformed, noisy, blurry"),
    "Background Black": ("(neutral black background), {prompt}", "ugly, deformed, noisy, blurry"),
    "Background White": ("(neutral white background), {prompt}", "ugly, deformed, noisy, blurry")
}

class ImageGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pollinations Image Generator")
        self.root.attributes("-topmost", True)
        self.root.geometry("520x640")
        self.root.resizable(True, True)  # Allow the window to be resizable

        # Predefined styles
        self.default_styles = list(style_tags.keys())
        self.user_styles = self.load_user_styles()
        self.styles = self.default_styles + [style.split(":")[0] for style in self.user_styles]

        # Create the menu bar
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)

        # Add the "Options" menu
        self.options_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="Options", menu=self.options_menu)
        
        # Add the "No Logo Password" option with entry field
        self.nologo_password_label = tk.Label(self.options_menu, text="No Logo Password (optional):")
        self.nologo_password_label.pack()
        self.nologo_password_entry = tk.Entry(self.options_menu)
        self.nologo_password_entry.pack()
        
        # Add a checkbutton to the "Options" menu
        self.always_on_top_var = tk.BooleanVar(value=True)
        self.options_menu.add_checkbutton(label="Always on Top", onvalue=True, offvalue=False, variable=self.always_on_top_var, command=self.toggle_always_on_top)

        # Add menu items for setting save path and updating script
        self.options_menu.add_command(label="Set Save Path", command=self.set_save_path)
        self.options_menu.add_command(label="Update Script", command=self.update_script)

        self.label = tk.Label(root, text="Enter your prompt and click 'GENERATE':")
        self.label.grid(row=0, column=0, columnspan=6, sticky="ew")

        self.prompt_entry = tk.Entry(root, justify='center')
        self.prompt_entry.grid(row=1, column=0, columnspan=6, sticky="ew")
        self.prompt_entry.bind("<Return>", self.on_generate_button_click)  # Bind Enter key to generate image

        # Consolidate enhance and private checkbuttons
        self.enhance_var = tk.BooleanVar(value=False)
        self.enhance_checkbutton = tk.Checkbutton(root, text="Enhance Image", variable=self.enhance_var)
        self.enhance_checkbutton.grid(row=2, column=0, columnspan=2, sticky="we")

        self.private_var = tk.BooleanVar(value=True)
        self.private_checkbutton = tk.Checkbutton(root, text="Private", variable=self.private_var)
        self.private_checkbutton.grid(row=2, column=2, columnspan=2, sticky="we")

        # Add seed and style on the same line
        self.seed_label = tk.Label(root, text="Seed:")
        self.seed_label.grid(row=3, column=0, columnspan=2, sticky="w", padx=20)

        self.seed_entry = tk.Entry(root, width=15)
        self.seed_entry.grid(row=3, column=0, sticky="w", padx=55)

        self.random_seed_var = tk.BooleanVar(value=True)
        self.random_seed_checkbutton = tk.Checkbutton(text="RANDOM", variable=self.random_seed_var, command=self.toggle_random_seed)
        self.random_seed_checkbutton.grid(row=3, column=0, sticky="e")

        self.style_var = tk.StringVar(value=self.default_styles[0])  # Set default style
        self.style_menu = tk.OptionMenu(root, self.style_var, *self.styles)
        self.style_menu.grid(row=3, column=2, columnspan=3, sticky="w")

        # Width and height options consolidated with ratio presets
        self.ratio_var = tk.StringVar(value="1:1")
        self.ratio_1_1 = tk.Radiobutton(root, text="1:1", variable=self.ratio_var, value="1:1", command=self.toggle_ratio, padx=50)
        self.ratio_1_1.grid(row=4, column=0, sticky="w")
        self.ratio_3_4 = tk.Radiobutton(root, text="3:4", variable=self.ratio_var, value="3:4", command=self.toggle_ratio)
        self.ratio_3_4.grid(row=4, column=1, sticky="w")
        self.ratio_16_9 = tk.Radiobutton(root, text="16:9", variable=self.ratio_var, value="16:9", command=self.toggle_ratio)
        self.ratio_16_9.grid(row=4, column=2, sticky="w")

        # Create the 'Custom' radio button
        self.ratio_custom = tk.Radiobutton(root, text="Custom", variable=self.ratio_var, value="Custom", command=self.toggle_ratio, padx=50)
        self.ratio_custom.grid(row=5, column=0, sticky="w")

        # Create and place the 'W:' label and entry
        self.custom_width_label = tk.Label(root, text="W:")
        self.custom_width_label.grid(row=5, column=1, sticky="w")
        self.custom_width_entry = tk.Entry(root, width=5)
        self.custom_width_entry.grid(row=5, column=1, sticky="w", padx=25)

        # Create and place the 'H:' label and entry
        self.custom_height_label = tk.Label(root, text="H:")
        self.custom_height_label.grid(row=5, column=2, sticky="w")
        self.custom_height_entry = tk.Entry(root, width=5)
        self.custom_height_entry.grid(row=5, column=2, sticky="w", padx=25)

        self.toggle_ratio()  # Set the initial state based on the selected ratio option

        self.custom_style_button = tk.Button(root, text="EDIT: USER STYLES", command=self.open_custom_styles_editor)
        self.custom_style_button.grid(row=6, column=0, columnspan=6, sticky="ew")

        self.generate_button = tk.Button(root, text="GENERATE", command=self.on_generate_button_click)
        self.generate_button.grid(row=7, column=0, columnspan=2, sticky="ew")

        self.copy_button = tk.Button(root, text="COPY", command=self.copy_to_clipboard)
        self.copy_button.grid(row=7, column=2, columnspan=4, sticky="ew")

        self.canvas = tk.Canvas(root, bg="white", width=512, height=512)
        self.canvas.grid(row=8, column=0, columnspan=6, sticky="nsew")

        # Add a status bar below options
        self.status_bar = tk.Label(root, text="", bg="lightgrey", height=1)
        self.status_bar.grid(row=9, column=0, columnspan=6, sticky="ew")

        self.image = None
        self.display_image_resized = None
        self.enlarged_window = None
        self.save_path = './GENERATED'  # Default save path

        self.root.bind("<Configure>", self.resize_image)

        # Configure grid to make canvas expandable
        self.root.grid_rowconfigure(8, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_columnconfigure(3, weight=1)
        self.root.grid_columnconfigure(4, weight=1)
        self.root.grid_columnconfigure(5, weight=1)

        self.previous_width = self.root.winfo_width()
        self.previous_height = self.root.winfo_height()

        self.root.update_idletasks()  # Ensure geometry is applied before further adjustments

        # Save settings on exit
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.load_settings()
        print("Initialization complete.")

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
            with open("user_styles.txt", "r") as file:
                user_styles = [line.strip() for line in file.readlines() if not line.strip().startswith("#")]
        print(f"Loaded user styles: {user_styles}")
        return user_styles

    def save_user_styles(self):
        print("Saving user styles...")
        with open("user_styles.txt", "w") as file:
            for style in self.user_styles:
                if not style.startswith("#"):
                    file.write(style + "\n")
        print("User styles saved.")

    def open_custom_styles_editor(self):
        editor_window = tk.Toplevel(self.root)
        editor_window.title("Custom Styles Editor")
        editor_window.geometry("600x430")
        editor_window.attributes("-topmost", True)

        # Create a text widget for editing the styles
        text_widget = tk.Text(editor_window)
        text_widget.pack(fill=tk.BOTH, expand=True)

        # Load current styles into the text widget
        try:
            with open("user_styles.txt", "r") as file:
                styles_content = file.read()
        except FileNotFoundError:
            styles_content = ""

        # Add an example format at the beginning of the text
        example_format = "# Example format:\n# Style Name: (trait1, trait2), (negative1, negative2)\n\n"
        text_widget.insert(tk.END, example_format + styles_content)

        def save_styles():
            new_styles_content = text_widget.get("1.0", tk.END)
            with open("user_styles.txt", "w") as file:
                file.write(new_styles_content.strip())
            self.user_styles = [line.strip() for line in new_styles_content.strip().split("\n") if not line.strip().startswith("#") and line.strip()]
            self.save_user_styles()
            self.update_style_menu()  # Update the styles dropdown menu
            editor_window.destroy()  # Close the editor window after saving

        save_button = tk.Button(editor_window, text="Save Styles", command=save_styles)
        save_button.pack(side=tk.BOTTOM, padx=10, pady=10)

        editor_window.protocol("WM_DELETE_WINDOW", save_styles)

    def update_style_menu(self):
        # Clear the current menu options
        self.style_menu['menu'].delete(0, 'end')

        # Combine default and user styles
        all_styles = self.default_styles + [style.split(":")[0] for style in self.user_styles]

        # Add new menu options
        for style in all_styles:
            self.style_menu['menu'].add_command(label=style, command=tk._setit(self.style_var, style))

        # Set the current style to the first style
        self.style_var.set(all_styles[0])

    def set_save_path(self):
        new_save_path = simpledialog.askstring("Set Save Path", "Enter the new save path:")
        if new_save_path:
            self.save_path = new_save_path
            self.status_bar.config(text=f"Save path set to: {self.save_path}")
            print(f"Save path set to: {self.save_path}")

    def update_script(self):
        update_url = "https://raw.githubusercontent.com/Tolerable/POLLI-GEN/main/POLLI-GEN.py"
        try:
            response = requests.get(update_url)
            response.raise_for_status()
            script_content = response.text
            backup_path = "POLLI-GEN_backup.py"
            with open(backup_path, "w") as backup_file:
                with open(__file__, "r") as current_file:
                    backup_file.write(current_file.read())
            with open(__file__, "w") as current_file:
                current_file.write(script_content)
            messagebox.showinfo("Update Successful", f"Script updated successfully.\nBackup saved as {backup_path}")
        except Exception as e:
            messagebox.showerror("Update Failed", f"Failed to update script. Error: {e}")

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
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    print(f"Failed to retrieve image from {url}. Error: {e}")
                    return None  # Return None if all attempts fail

    async def generate_images_async(self, urls):
        print(f"Generating images async for URLs: {urls}")
        tasks = [self.async_generate_image(url) for url in urls]
        return await asyncio.gather(*tasks)

    async def generate_image(self):
        print("Generate image button clicked.")
        self.status_bar.config(text="IN QUEUE, WAITING FOR IMAGE...")
        prompt = self.prompt_entry.get()
        print(f"Prompt entered: {prompt}")
        if not prompt:
            messagebox.showerror("Error", "Please enter a prompt")
            self.status_bar.config(text="")
            return
        
        # Add visual style to the prompt if selected
        style = self.style_var.get()
        print(f"User selected style: {style}")
        if style not in style_tags and style not in [s.split(":")[0] for s in self.user_styles]:
            messagebox.showerror("Error", "Selected style is not valid")
            self.status_bar.config(text="")
            return

        # Combine style and prompt using style tags
        if style in style_tags:
            style_prompt, _ = style_tags[style]
        else:
            style_prompt, _ = self.user_styles[[s.split(":")[0] for s in self.user_styles].index(style)].split(":")[1].split("),")
            style_prompt = style_prompt + "), {prompt}"
            
        full_prompt = style_prompt.format(prompt=prompt)

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

        params.append(f"enhance={str(self.enhance_var.get()).lower()}")  # Explicitly set enhance to true or false
        
        url = f"https://image.pollinations.ai/prompt/{requests.utils.quote(full_prompt)}?{'&'.join(params)}"
        print(f"Sending request to URL: {url}")

        try:
            images = await self.generate_images_async([url])
            images = [img for img in images if img is not None]
            if images:
                print(f"Image received")
                self.image = images[0]  # Store the original image
                self.display_image(self.image)
                self.save_image(self.image)
            else:
                messagebox.showerror("Error", "Failed to retrieve image after multiple attempts.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to retrieve image. Error: {e}")
        finally:
            self.status_bar.config(text="Image generation complete.")
            print("Status bar reset.")

    def display_image(self, image):
        print("Displaying image...")
        self.canvas.delete("all")
        self.tk_images = []
        
        # Resize to 512x512 for display
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
        self.root.geometry(f"{canvas_width+40}x{canvas_height+280}")  # Adjusting for the GUI elements size

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
        self.status_bar.config(text=f"Image saved to: {self.saved_image_path}")
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
        if self.enlarged_window and self.enlarged_window.winfo_exists():
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
            with open("settings.txt", "r") as file:
                settings = file.read().splitlines()
                if settings:
                    self.nologo_password_entry.insert(0, settings[0] if len(settings) > 0 else "")
                    self.private_var.set(settings[1] == 'True' if len(settings) > 1 else False)
                    self.seed_entry.insert(0, settings[2] if len(settings) > 2 else "")
                    self.style_var.set(settings[3] if len(settings) > 3 else self.default_styles[0])  # Ensure default style
                    self.enhance_var.set(settings[4] == 'True' if len(settings) > 4 else False)
                    self.ratio_var.set(settings[5] if len(settings) > 5 else "1:1")
                    if len(settings) > 6:
                        self.custom_width_entry.insert(0, settings[6])
                    if len(settings) > 7:
                        self.custom_height_entry.insert(0, settings[7])
                    if len(settings) > 8:
                        self.save_path = settings[8]
        print("Settings loaded.")

    def save_settings(self):
        print("Saving settings...")
        with open("settings.txt", "w") as file:
            file.write(f"{self.nologo_password_entry.get()}\n")
            file.write(f"{self.private_var.get()}\n")
            file.write(f"{self.seed_entry.get()}\n")
            file.write(f"{self.style_var.get()}\n")
            file.write(f"{self.enhance_var.get()}\n")
            file.write(f"{self.ratio_var.get()}\n")
            file.write(f"{self.custom_width_entry.get()}\n")
            file.write(f"{self.custom_height_entry.get()}\n")
            file.write(f"{self.save_path}\n")
        print("Settings saved.")

    def on_closing(self):
        print("Closing application...")
        self.save_settings()
        self.root.destroy()
        print("Application closed.")

    def on_generate_button_click(self, event=None):
        print("Generate button clicked. Calling generate_image()...")
        asyncio.run(self.generate_image())

if __name__ == "__main__":
    print("Starting application...")
    root = tk.Tk()
    app = ImageGeneratorApp(root)
    root.mainloop()
    print("Application started.")
