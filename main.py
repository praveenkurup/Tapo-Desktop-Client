import tkinter as tk
from tkinter import ttk
import os
import threading
from dotenv import load_dotenv
from settings_page import SettingsPage
from api import get_all_devices, get_device_details, get_presets, move_to_preset, move_camera
from video_player import VideoPlayer
from PIL import Image, ImageTk
import sys

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller."""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Tapo Desktop Client")
        self.root.geometry("1200x800")
        self.root.configure(bg="#0a0a0a")
        
        # Color scheme - Black theme
        self.bg_dark = "#0a0a0a"
        self.bg_darker = "#000000"
        self.bg_card = "#1a1a1a"
        self.bg_header = "#111111"
        self.text_primary = "#ffffff"
        self.text_secondary = "#b0b0b0"
        self.accent = "#00d4ff"
        self.accent_hover = "#00b8e6"
        self.success = "#00ff88"
        self.error = "#ff4444"
        
        # Load environment variables
        # Load .env file
        dotenv_path = resource_path(".env")
        load_dotenv(dotenv_path)
        
        # Store devices data
        self.devices_data = []
        self.selected_device = None
        self.selected_camera_frame = None  # Track selected camera frame
        self.video_player = None
        self.current_presets = {}  # Store current camera presets
        self.right_sidebar = None  # Right sidebar for presets
        
        # Create main frame
        self.main_frame = tk.Frame(self.root, bg=self.bg_dark)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create header with settings icon
        self.create_header()
        
        # Create main content area with sidebar
        self.create_main_content()

        self.create_footer()
        
        # Settings page (initially hidden)
        self.settings_page = None
        
        # Load devices on startup
        self.load_devices()
        
    def create_header(self):
        header_frame = tk.Frame(self.main_frame, bg=self.bg_header, height=70)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Add subtle border effect
        border_frame = tk.Frame(header_frame, bg="#1a1a1a", height=1)
        border_frame.pack(side=tk.BOTTOM, fill=tk.X)

        # Load logo
        logo_img = Image.open(resource_path("logo.png"))  # replace with your logo path
        logo_img = logo_img.resize((40, 40), Image.Resampling.LANCZOS)  # updated
        self.logo_photo = ImageTk.PhotoImage(logo_img)  # keep reference

        # Logo label
        logo_label = tk.Label(header_frame, image=self.logo_photo, bg=self.bg_header)
        logo_label.pack(side=tk.LEFT, padx=(20, 10), pady=15)

        # Title
        title_label = tk.Label(
            header_frame,
            text="Tapo Desktop Client",
            font=("Segoe UI", 20, "bold"),
            bg=self.bg_header,
            fg=self.text_primary
        )
        title_label.pack(side=tk.LEFT, pady=20)
        
       # Settings button
        settings_btn = tk.Button(
            header_frame,
            text="⚙",  # Gear icon for settings
            font=("Segoe UI", 18),
            bg=self.bg_header,
            fg=self.text_primary,
            activebackground=self.accent_hover,
            activeforeground=self.bg_dark,
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self.open_settings
        )
        settings_btn.pack(side=tk.RIGHT, padx=20, pady=15)

        # Add hover effect (optional, but improves UX)
        def on_enter_settings(e):
            settings_btn.config(fg=self.accent)
        def on_leave_settings(e):
            settings_btn.config(fg=self.text_primary)
        settings_btn.bind("<Enter>", on_enter_settings)
        settings_btn.bind("<Leave>", on_leave_settings)

    def create_footer(self):
        """Create a full-width footer strip with centered clickable name"""
        footer_frame = tk.Frame(self.root, bg=self.bg_header, height=40)
        footer_frame.pack(side=tk.BOTTOM, fill=tk.X)
        footer_frame.pack_propagate(False)

        # Center container frame
        center_frame = tk.Frame(footer_frame, bg=self.bg_header)
        center_frame.place(relx=0.5, rely=0.5, anchor="center")  # centers horizontally and vertically

        # "Made with love by " label
        text_label = tk.Label(
            center_frame,
            text="Made with love by ",
            font=("Segoe UI", 11),
            bg=self.bg_header,
            fg=self.text_primary
        )
        text_label.pack(side=tk.LEFT)

        # "Praveen" in blue, clickable
        name_label = tk.Label(
            center_frame,
            text="Praveen",
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_header,
            fg=self.accent,
            cursor="hand2"
        )
        name_label.pack(side=tk.LEFT)

        # Function to show socials popup
        def show_socials():
            popup = tk.Toplevel(self.root)
            popup.title("Connect with me")
            popup.geometry("350x150")
            popup.configure(bg=self.bg_card)
            popup.resizable(False, False)

            # Email
            email_label = tk.Label(
                popup,
                text="Email: username.praveen.email@gmail.com",
                font=("Segoe UI", 10),
                bg=self.bg_card,
                fg=self.text_primary,
                cursor="hand2"
            )
            email_label.pack(anchor="w", padx=15, pady=(10,5))
            email_label.bind("<Button-1>", lambda e: __import__('webbrowser').open("mailto:username.praveen.email@gmail.com"))

            # GitHub
            github_label = tk.Label(
                popup,
                text="GitHub: https://github.com/praveenkurup",
                font=("Segoe UI", 10),
                bg=self.bg_card,
                fg=self.text_primary,
                cursor="hand2"
            )
            github_label.pack(anchor="w", padx=15, pady=5)
            github_label.bind("<Button-1>", lambda e: __import__('webbrowser').open("https://github.com/praveenkurup"))

            # X / Twitter
            x_label = tk.Label(
                popup,
                text="X: https://x.com/real_praveenk",
                font=("Segoe UI", 10),
                bg=self.bg_card,
                fg=self.text_primary,
                cursor="hand2"
            )
            x_label.pack(anchor="w", padx=15, pady=5)
            x_label.bind("<Button-1>", lambda e: __import__('webbrowser').open("https://x.com/real_praveenk"))

        # Bind click to name
        name_label.bind("<Button-1>", lambda e: show_socials())




        
    def create_main_content(self):
        """Create main content area with sidebar"""
        # Main content container
        content_container = tk.Frame(self.main_frame, bg=self.bg_dark)
        content_container.pack(fill=tk.BOTH, expand=True)
        content_container.grid_rowconfigure(0, weight=1)
        content_container.grid_columnconfigure(1, weight=1)  # Center column gets extra space
        
        # Left sidebar for cameras
        left_frame = tk.Frame(content_container, bg=self.bg_dark)
        left_frame.grid(row=0, column=0, sticky="nsew")
        self.create_sidebar(left_frame)
        
        # Right content area (center)
        center_frame = tk.Frame(content_container, bg=self.bg_dark)
        center_frame.grid(row=0, column=1, sticky="nsew")
        center_frame.grid_rowconfigure(0, weight=1)
        center_frame.grid_columnconfigure(0, weight=1)
        self.create_right_content(center_frame)
        
        # Right sidebar for presets (initially hidden)
        right_frame = tk.Frame(content_container, bg=self.bg_dark)
        right_frame.grid(row=0, column=2, sticky="nsew")
        self.create_presets_sidebar(right_frame)
        
        # Check if .env is configured
        self.check_env_config()
    
    def create_sidebar(self, parent):
        """Create left sidebar for camera list"""
        # Sidebar frame
        sidebar_frame = tk.Frame(parent, bg=self.bg_card, width=250)
        sidebar_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        sidebar_frame.pack_propagate(False)
        
        # Sidebar header
        sidebar_header = tk.Frame(sidebar_frame, bg=self.bg_header, height=50)
        sidebar_header.pack(fill=tk.X)
        sidebar_header.pack_propagate(False)
        
        sidebar_title = tk.Label(
            sidebar_header,
            text="Cameras",
            font=("Segoe UI", 14, "bold"),
            bg=self.bg_header,
            fg=self.text_primary
        )
        sidebar_title.pack(pady=15)
        
        # Scrollable frame for camera list
        canvas = tk.Canvas(sidebar_frame, bg=self.bg_card, highlightthickness=0)
        scrollbar = tk.Scrollbar(sidebar_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.bg_card)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        self.canvas = canvas  # store reference

        
        self.canvas_window = canvas.create_window(
            (0, 0),
            window=scrollable_frame,
            anchor="nw"
        )

        def on_canvas_configure(event):
            canvas.itemconfig(self.canvas_window, width=event.width)

        canvas.bind("<Configure>", on_canvas_configure)


        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.camera_list_frame = scrollable_frame
        
        # Loading label (will be updated when devices load)
        self.loading_label = tk.Label(
            scrollable_frame,
            text="Loading cameras...",
            font=("Segoe UI", 11),
            bg=self.bg_card,
            fg=self.text_secondary
        )
        self.loading_label.pack(pady=20)

    
    def create_right_content(self, parent):
        """Create right content area"""
        self.right_content = tk.Frame(parent, bg=self.bg_dark)
        self.right_content.pack(fill=tk.BOTH, expand=True)
        self.right_content.grid_rowconfigure(0, weight=1)
        self.right_content.grid_columnconfigure(0, weight=1)
        
        # No camera selected message (centered)
        self.no_camera_label = tk.Label(
            self.right_content,
            text="No camera selected",
            font=("Segoe UI", 16),
            bg=self.bg_dark,
            fg=self.text_secondary
        )
        self.no_camera_label.grid(row=0, column=0, sticky="nsew")
        
        # Initialize video player (hidden initially)
        self.video_player = VideoPlayer(self.right_content, self.bg_dark)
        self.video_player.video_frame.grid_remove()
        
    def create_presets_sidebar(self, parent):
        """Create right sidebar for presets"""
        # Presets sidebar frame
        self.right_sidebar = tk.Frame(parent, bg=self.bg_card, width=250)
        # Don't pack it initially - it will be shown when a camera is selected
        self.right_sidebar.pack_propagate(False)
        
        # Sidebar header
        sidebar_header = tk.Frame(self.right_sidebar, bg=self.bg_header, height=50)
        sidebar_header.pack(fill=tk.X)
        sidebar_header.pack_propagate(False)
        
        sidebar_title = tk.Label(
            sidebar_header,
            text="Controls",
            font=("Segoe UI", 14, "bold"),
            bg=self.bg_header,
            fg=self.text_primary
        )
        sidebar_title.pack(pady=15)
        
        # Create joystick control
        self.create_joystick_control(self.right_sidebar)
        
        # Divider
        divider = tk.Frame(self.right_sidebar, bg="#2a2a2a", height=1)
        divider.pack(fill=tk.X, pady=10)
        
        # Presets label
        presets_label = tk.Label(
            self.right_sidebar,
            text="Presets",
            font=("Segoe UI", 11, "bold"),
            bg=self.bg_card,
            fg=self.text_primary
        )
        presets_label.pack(pady=(10, 5))
        
        # Scrollable frame for presets list
        canvas = tk.Canvas(self.right_sidebar, bg=self.bg_card, highlightthickness=0)
        scrollbar = tk.Scrollbar(self.right_sidebar, orient="vertical", command=canvas.yview)
        self.presets_frame = tk.Frame(canvas, bg=self.bg_card)
        
        self.presets_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        self.presets_canvas_window = canvas.create_window(
            (0, 0),
            window=self.presets_frame,
            anchor="nw"
        )
        
        def on_canvas_configure(event):
            canvas.itemconfig(self.presets_canvas_window, width=event.width)
        
        canvas.bind("<Configure>", on_canvas_configure)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def create_joystick_control(self, parent):
        """Create joystick control with directional buttons"""
        # Joystick container
        joystick_container = tk.Frame(parent, bg=self.bg_card)
        joystick_container.pack(pady=10, padx=10)
        
        # Create 3x3 grid for joystick
        joystick_frame = tk.Frame(joystick_container, bg=self.bg_card)
        joystick_frame.pack()
        
        # Button size - much smaller
        btn_width = 4
        btn_height = 1
        
        # Up button
        up_btn = tk.Button(
            joystick_frame,
            text="↑",
            font=("Segoe UI", 12, "bold"),
            width=btn_width,
            height=btn_height,
            bg=self.bg_card,
            fg=self.accent,
            activebackground=self.accent,
            activeforeground=self.bg_dark,
            relief=tk.RAISED,
            cursor="hand2",
            bd=1,
            command=lambda: self.move_camera_direction('y', 10)
        )
        up_btn.grid(row=0, column=1, padx=2, pady=2)
        
        # Left button
        left_btn = tk.Button(
            joystick_frame,
            text="←",
            font=("Segoe UI", 12, "bold"),
            width=btn_width,
            height=btn_height,
            bg=self.bg_card,
            fg=self.accent,
            activebackground=self.accent,
            activeforeground=self.bg_dark,
            relief=tk.RAISED,
            cursor="hand2",
            bd=1,
            command=lambda: self.move_camera_direction('x', -10)
        )
        left_btn.grid(row=1, column=0, padx=2, pady=2)
        
        # Center button (stop)
        center_btn = tk.Button(
            joystick_frame,
            text="⊙",
            font=("Segoe UI", 10, "bold"),
            width=btn_width,
            height=btn_height,
            bg=self.bg_card,
            fg=self.text_secondary,
            activebackground=self.text_secondary,
            activeforeground=self.bg_dark,
            relief=tk.RAISED,
            cursor="hand2",
            bd=1
        )
        center_btn.grid(row=1, column=1, padx=2, pady=2)
        
        # Right button
        right_btn = tk.Button(
            joystick_frame,
            text="→",
            font=("Segoe UI", 12, "bold"),
            width=btn_width,
            height=btn_height,
            bg=self.bg_card,
            fg=self.accent,
            activebackground=self.accent,
            activeforeground=self.bg_dark,
            relief=tk.RAISED,
            cursor="hand2",
            bd=1,
            command=lambda: self.move_camera_direction('x', 10)
        )
        right_btn.grid(row=1, column=2, padx=2, pady=2)
        
        # Down button
        down_btn = tk.Button(
            joystick_frame,
            text="↓",
            font=("Segoe UI", 12, "bold"),
            width=btn_width,
            height=btn_height,
            bg=self.bg_card,
            fg=self.accent,
            activebackground=self.accent,
            activeforeground=self.bg_dark,
            relief=tk.RAISED,
            cursor="hand2",
            bd=1,
            command=lambda: self.move_camera_direction('y', -10)
        )
        down_btn.grid(row=2, column=1, padx=2, pady=2)
    
    def move_camera_direction(self, axis, value):
        """Send move camera request"""
        if not self.selected_device:
            return
        
        device_id = self.selected_device.get('device_id')
        
        # Send request in separate thread
        def send_request():
            try:
                result = move_camera(device_id, axis, value)
                if result:
                    print(f"Successfully moved camera on {axis}-axis by {value}")
                else:
                    print(f"Failed to move camera on {axis}-axis")
            except Exception as e:
                print(f"Error moving camera: {e}")
        
        thread = threading.Thread(target=send_request, daemon=True)
        thread.start()
        
    def create_preset_button(self, preset_id, preset_name):
        """Create a preset button"""
        preset_btn = tk.Button(
            self.presets_frame,
            text=preset_name,
            font=("Segoe UI", 11),
            bg=self.bg_card,
            fg=self.text_primary,
            activebackground=self.accent,
            activeforeground=self.bg_dark,
            relief=tk.FLAT,
            cursor="hand2",
            padx=15,
            pady=12,
            bd=0,
            highlightthickness=0,
            command=lambda pid=preset_id: self.move_to_preset(pid)
        )
        preset_btn.pack(fill=tk.X, pady=5, padx=10)
        
        # Add hover effect
        def on_enter(e):
            preset_btn.config(bg="#2a2a2a")
        def on_leave(e):
            preset_btn.config(bg=self.bg_card)
        preset_btn.bind("<Enter>", on_enter)
        preset_btn.bind("<Leave>", on_leave)
        
        return preset_btn
    
    def load_presets(self):
        """Load presets for the selected camera"""
        if not self.selected_device:
            return
        
        device_id = self.selected_device.get('device_id')
        
        # Clear existing presets
        for widget in self.presets_frame.winfo_children():
            widget.destroy()
        
        # Show loading message
        loading_label = tk.Label(
            self.presets_frame,
            text="Loading presets...",
            font=("Segoe UI", 11),
            bg=self.bg_card,
            fg=self.text_secondary
        )
        loading_label.pack(pady=20)
        
        # Load presets in separate thread
        def fetch_presets():
            try:
                presets = get_presets(device_id)
                self.current_presets = presets or {}
                
                # Update UI in main thread
                self.root.after(0, lambda: self.update_presets_display())
            except Exception as e:
                print(f"Error loading presets: {e}")
                self.root.after(0, lambda: loading_label.config(
                    text="Error loading presets",
                    fg=self.error
                ))
        
        thread = threading.Thread(target=fetch_presets, daemon=True)
        thread.start()
    
    def update_presets_display(self):
        """Update the presets display"""
        # Clear existing widgets
        for widget in self.presets_frame.winfo_children():
            widget.destroy()
        
        if not self.current_presets:
            no_presets_label = tk.Label(
                self.presets_frame,
                text="No presets available",
                font=("Segoe UI", 11),
                bg=self.bg_card,
                fg=self.text_secondary
            )
            no_presets_label.pack(pady=20)
            return
        
        # Create buttons for each preset
        for preset_id, preset_name in self.current_presets.items():
            self.create_preset_button(preset_id, preset_name)
    
    def move_to_preset(self, preset_id):
        """Send move to preset request"""
        if not self.selected_device:
            return
        
        device_id = self.selected_device.get('device_id')
        
        # Send request in separate thread
        def send_request():
            try:
                result = move_to_preset(device_id, preset_id)
                if result:
                    print(f"Successfully moved to preset {preset_id}")
                else:
                    print(f"Failed to move to preset {preset_id}")
            except Exception as e:
                print(f"Error moving to preset: {e}")
        
        thread = threading.Thread(target=send_request, daemon=True)
        thread.start()
        
    def check_env_config(self):
        """Check if environment variables are configured"""
        # Just check silently, no UI message needed
        pass
    
    def open_settings(self):
        """Open settings page"""
        if self.settings_page is None:
            self.settings_page = SettingsPage(self.root, self)
        else:
            self.settings_page.show()
    
    def load_devices(self):
        """Load all devices and their details"""
        # Check if credentials are configured
        authorization = os.getenv("Authorization")
        x_term_id = os.getenv("X-Term-Id")
        
        if not authorization or not x_term_id:
            self.loading_label.config(
                text="⚠ Configure settings first",
                fg=self.error
            )
            return
        
        # Update loading status
        self.loading_label.config(
            text="Loading cameras...",
            fg=self.text_secondary
        )
        
        # Load devices in a separate thread to avoid blocking UI
        def fetch_devices():
            try:
                print("Starting to fetch devices...")
                # Get all device IDs
                device_ids = get_all_devices()
                print(f"get_all_devices returned: {device_ids}")
                
                if not device_ids or device_ids == False:
                    print("No device IDs returned")
                    self.root.after(0, lambda: self.loading_label.config(
                        text="No devices found",
                        fg=self.error
                    ))
                    return
                
                if not isinstance(device_ids, list) or len(device_ids) == 0:
                    print(f"Device IDs is not a valid list: {type(device_ids)}, length: {len(device_ids) if isinstance(device_ids, list) else 'N/A'}")
                    self.root.after(0, lambda: self.loading_label.config(
                        text="No devices found",
                        fg=self.error
                    ))
                    return
                
                print(f"Found {len(device_ids)} device IDs: {device_ids}")
                
                # Get details for each device
                devices_data = []
                for device_id in device_ids:
                    try:
                        print(f"Getting details for device: {device_id}")
                        device_details = get_device_details(device_id)
                        print(f"Device details for {device_id}: {device_details}")
                        if device_details and device_details != False:
                            device_details['device_id'] = device_id
                            devices_data.append(device_details)
                            print(f"Added device {device_id} to list")
                    except Exception as e:
                        # Continue with other devices if one fails
                        print(f"Error getting details for {device_id}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                print(f"Total devices with details: {len(devices_data)}")
                
                # Update UI in main thread - fix closure issue
                devices_data_copy = devices_data.copy()
                if devices_data_copy:
                    self.root.after(0, lambda data=devices_data_copy: self.update_camera_list(data))
                else:
                    self.root.after(0, lambda: self.loading_label.config(
                        text="No device details retrieved",
                        fg=self.error
                    ))
                
            except Exception as e:
                import traceback
                error_msg = str(e)
                print(f"Exception in fetch_devices: {error_msg}")
                traceback.print_exc()
                self.root.after(0, lambda msg=error_msg: self.loading_label.config(
                    text=f"Error: {msg}",
                    fg=self.error
                ))
        
        # Start thread
        thread = threading.Thread(target=fetch_devices, daemon=True)
        thread.start()
    
    def update_camera_list(self, devices_data):
        """Update the camera list in the sidebar"""
        print(f"update_camera_list called with {len(devices_data) if devices_data else 0} devices")
        
        # Store previously selected device ID
        previously_selected_id = None
        if self.selected_device:
            previously_selected_id = self.selected_device.get('device_id')
        
        # Stop video stream if playing
        if self.video_player:
            self.video_player.stop_stream()
        
        # Hide video player and show "No camera selected"
        if self.video_player and self.video_player.video_frame:
            self.video_player.video_frame.grid_remove()
        self.no_camera_label.grid(row=0, column=0, sticky="nsew")
        
        # Hide presets sidebar
        self.right_sidebar.pack_forget()
        
        self.devices_data = devices_data
        
        # Clear existing items (including loading label)
        for widget in self.camera_list_frame.winfo_children():
            widget.destroy()
        
        # Reset selection
        self.selected_device = None
        self.selected_camera_frame = None
        
        if not devices_data or len(devices_data) == 0:
            print("No devices data, showing 'No cameras found'")
            no_devices_label = tk.Label(
                self.camera_list_frame,
                text="No cameras found",
                font=("Segoe UI", 11),
                bg=self.bg_card,
                fg=self.text_secondary
            )
            no_devices_label.pack(pady=20)
            return
        
        print(f"Creating camera items for {len(devices_data)} devices")
        
        # Create camera items
        item_frames = {}
        for idx, device in enumerate(devices_data):
            item_frame = self.create_camera_item(device, idx)
            device_id = device.get('device_id')
            if device_id:
                item_frames[device_id] = (device, item_frame)
        
        # Auto-select if this was the previously selected device
        if previously_selected_id and previously_selected_id in item_frames:
            device, item_frame = item_frames[previously_selected_id]
            self.select_camera(device, item_frame)
    
    def create_camera_item(self, device, index):
        """Create a camera item in the sidebar"""
        # Camera item frame
        item_frame = tk.Frame(
            self.camera_list_frame,
            bg=self.bg_card,
            relief=tk.FLAT
        )
        item_frame.pack(fill=tk.X, pady=5)  # Removed padx=10 to allow full width selection
        
        # Store device reference in frame
        item_frame.device = device
        item_frame.device_id = device.get('device_id')
        
        # Camera name
        name = device.get('name', 'Unknown Camera')
        name_label = tk.Label(
            item_frame,
            text=name,
            font=("Segoe UI", 12, "bold"),
            bg=self.bg_card,
            fg=self.text_primary,
            anchor="w"
        )
        name_label.pack(fill=tk.X, padx=25, pady=(12, 4))  # Increased padx to compensate for removed frame padding
        
        # Device name
        device_name = device.get('device_name', 'Unknown Device')
        device_label = tk.Label(
            item_frame,
            text=device_name,
            font=("Segoe UI", 10),
            bg=self.bg_card,
            fg=self.text_secondary,
            anchor="w"
        )
        device_label.pack(fill=tk.X, padx=25, pady=(0, 12))  # Increased padx to compensate for removed frame padding
        
        # Make clickable
        def on_click(e):
            self.select_camera(device, item_frame)
        
        # Bind click to frame and labels
        item_frame.bind("<Button-1>", on_click)
        name_label.bind("<Button-1>", on_click)
        device_label.bind("<Button-1>", on_click)
        
        # Change cursor on hover
        item_frame.bind("<Enter>", lambda e: item_frame.config(cursor="hand2"))
        item_frame.bind("<Leave>", lambda e: item_frame.config(cursor=""))
        name_label.bind("<Enter>", lambda e: item_frame.config(cursor="hand2"))
        name_label.bind("<Leave>", lambda e: item_frame.config(cursor=""))
        device_label.bind("<Enter>", lambda e: item_frame.config(cursor="hand2"))
        device_label.bind("<Leave>", lambda e: item_frame.config(cursor=""))
        
        return item_frame
    
    def select_camera(self, device, item_frame):
        """Handle camera selection"""
        # Reset all camera items to default background and remove selection indicators
        for widget in self.camera_list_frame.winfo_children():
            if isinstance(widget, tk.Frame) and hasattr(widget, 'device_id'):
                widget.config(bg=self.bg_card, highlightthickness=0, highlightbackground=self.bg_card)
                # Reset all child labels
                for child in widget.winfo_children():
                    if isinstance(child, tk.Label):
                        child.config(bg=self.bg_card)
        
        # Set selected camera with accent border
        item_frame.config(
            bg=self.bg_card,
            highlightthickness=3,
            highlightbackground=self.accent,
            highlightcolor=self.accent
        )
        
        # Update all child labels to match
        for child in item_frame.winfo_children():
            if isinstance(child, tk.Label):
                child.config(bg=self.bg_card)
        
        self.selected_device = device
        self.selected_camera_frame = item_frame
        
        # Show video player and hide "No camera selected" message
        self.no_camera_label.grid_remove()
        if self.video_player and self.video_player.video_frame:
            self.video_player.video_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            # Start playing stream
            self.video_player.play_stream(device)
        
        # Show presets sidebar and load presets
        self.right_sidebar.pack(side=tk.LEFT, fill=tk.Y, expand=False)
        self.load_presets()
    
    def show_main_page(self):
        """Show main page and hide settings"""
        if self.settings_page:
            self.settings_page.hide()
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        self.check_env_config()
        # Reload devices if needed
        if not self.devices_data:
            self.load_devices()
        # Restore camera selection state if a camera was selected
        if self.selected_device and self.selected_camera_frame:
            # Re-select the camera to restore video stream
            self.select_camera(self.selected_device, self.selected_camera_frame)

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap(resource_path("logo.ico"))
    app = MainApp(root)
    root.mainloop()

