# video_player.py - UPDATED WITH PRIVACY MODE BUTTON
import tkinter as tk
import threading
import sys
import time
import vlc
from rtsp_config import get_rtsp_config, build_rtsp_url
from api import toggle_privacy_mode  # Import the new function

class VideoPlayer:
    def __init__(self, parent, bg_color="#0a0a0a"):
        self.parent = parent
        self.bg_color = bg_color
        self.video_frame = None
        self.is_playing = False
        self.is_muted = False
        self.is_privacy_enabled = False  # Track current privacy state
        self.current_device = None
        self.stream_id = 0
        # VLC objects
        self.instance = None
        self.player = None
        self.create_video_frame()

    def create_video_frame(self):
        """Create the frame and label that will host the VLC video"""
        self.video_frame = tk.Frame(self.parent, bg=self.bg_color)
        # Video surface
        self.video_label = tk.Label(
            self.video_frame,
            bg=self.bg_color,
            anchor="center"
        )
        self.video_label.pack(fill=tk.BOTH, expand=True)

        # Mute button
        self.mute_button = tk.Button(
            self.video_frame,
            text="🔊",
            font=("Segoe UI", 18),
            bg="#2a2a2a",
            fg="white",
            activebackground="#3a3a3a",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self.toggle_mute
        )
        self.mute_button.place(relx=1.0, rely=1.0, x=-80, y=-20, anchor="se")  # Shifted left
        self.mute_button.place_forget()

        # Privacy Mode button
        self.privacy_button = tk.Button(
            self.video_frame,
            text="🔓",  # Open = privacy OFF
            font=("Segoe UI", 18),
            bg="#2a2a2a",
            fg="white",
            activebackground="#3a3a3a",
            activeforeground="white",
            relief=tk.FLAT,
            bd=0,
            cursor="hand2",
            command=self.toggle_privacy
        )
        self.privacy_button.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")
        self.privacy_button.place_forget()

    def toggle_mute(self):
        """Toggle mute/unmute"""
        if not self.player:
            return
        self.is_muted = not self.is_muted
        volume = 0 if self.is_muted else 100
        try:
            self.player.audio_set_volume(volume)
        except:
            pass
        self.mute_button.config(text="🔇" if self.is_muted else "🔊")

    def toggle_privacy(self):
        """Toggle privacy mode via API"""
        if not self.current_device:
            return

        device_id = self.current_device.get('device_id')
        new_state = not self.is_privacy_enabled

        # Optimistic UI update
        self.is_privacy_enabled = new_state
        self.privacy_button.config(text="🔒" if new_state else "🔓")

        def send_privacy_request():
            success = toggle_privacy_mode(device_id, new_state)
            if not success and self.stream_id == self.stream_id:  # Revert on failure
                self.parent.after(0, lambda: (
                    setattr(self, 'is_privacy_enabled', not new_state),
                    self.privacy_button.config(text="🔒" if not new_state else "🔓")
                ))

        threading.Thread(target=send_privacy_request, daemon=True).start()

    def play_stream(self, device):
        """Start playing the RTSP stream"""
        self.stop_stream()
        self.stream_id += 1
        local_stream_id = self.stream_id
        self.current_device = device
        device_id = device.get('device_id')

        rtsp_config = get_rtsp_config(device_id)
        rtsp_url = build_rtsp_url(device_id, device, rtsp_config)

        if not rtsp_url:
            self.video_label.config(
                text="RTSP not configured",
                fg="#ff4444",
                font=("Segoe UI", 14)
            )
            self.mute_button.place_forget()
            self.privacy_button.place_forget()
            return

        self.video_label.config(
            text="Connecting to stream...\n(Video + Audio)",
            fg="#b0b0b0",
            font=("Segoe UI", 12)
        )

        # Show buttons
        self.is_muted = False
        self.mute_button.config(text="🔊")
        self.mute_button.place(relx=1.0, rely=1.0, x=-80, y=-20, anchor="se")
        self.mute_button.lift()

        # Default: assume privacy off (you can enhance this later by querying state)
        self.is_privacy_enabled = False
        self.privacy_button.config(text="🔓")
        self.privacy_button.place(relx=1.0, rely=1.0, x=-20, y=-20, anchor="se")
        self.privacy_button.lift()

        self.is_playing = True

        thread = threading.Thread(
            target=self._start_vlc_player,
            args=(rtsp_url, local_stream_id),
            daemon=True
        )
        thread.start()

    def _start_vlc_player(self, rtsp_url, stream_id):
        """VLC playback logic (unchanged except safe volume)"""
        if stream_id != self.stream_id:
            return
        try:
            vlc_options = [
                '--quiet',
                '--rtsp-tcp',
                '--network-caching=1000',
                '--rtsp-frame-buffer-size=1000000',
                '--no-video-title-show',
                '--intf=dummy',
                '--extraintf=',
                '--no-disable-screensaver',
                '--aout=directsound',
            ]
            self.instance = vlc.Instance(*vlc_options)
            if not self.instance:
                raise Exception("Failed to create VLC instance")
            self.player = self.instance.media_player_new()
            if not self.player:
                raise Exception("Failed to create media player")
            media = self.instance.media_new(rtsp_url)
            self.player.set_media(media)

            if sys.platform == "win32":
                hwnd = self.video_label.winfo_id()
                self.player.set_hwnd(hwnd)
            elif sys.platform == "darwin":
                nsobject = self.video_label.winfo_id()
                self.player.set_nsobject(nsobject)
            elif sys.platform.startswith("linux"):
                xid = self.video_label.winfo_id()
                self.player.set_xwindow(xid)

            result = self.player.play()
            if result == -1:
                raise Exception("VLC failed to start playback")

            volume = 0 if self.is_muted else 100
            self.player.audio_set_volume(volume)

            time.sleep(1.0)
            if stream_id == self.stream_id:
                self.parent.after(0, lambda: self.video_label.config(text=""))

            while stream_id == self.stream_id and self.player.is_playing():
                time.sleep(0.2)

        except Exception as e:
            print(f"[VLC Error] {e}")
            if stream_id == self.stream_id:
                self.parent.after(0, lambda: self._show_error(str(e), stream_id))

    def _show_error(self, message, stream_id):
        if stream_id != self.stream_id:
            return
        self.video_label.config(
            text=f"Stream Error\n{message}",
            fg="#ff4444",
            font=("Segoe UI", 12)
        )

    def stop_stream(self):
        """Stop stream cleanly"""
        self.stream_id += 1
        self.is_playing = False
        if self.player:
            try:
                self.player.stop()
                self.player.release()
            except:
                pass
            self.player = None
        if self.instance:
            try:
                self.instance.release()
            except:
                pass
            self.instance = None

        self.mute_button.place_forget()
        self.privacy_button.place_forget()
        self.video_label.config(
            text="No stream",
            fg="#b0b0b0",
            font=("Segoe UI", 12)
        )

    def destroy(self):
        self.stop_stream()