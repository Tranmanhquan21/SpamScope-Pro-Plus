import customtkinter as ctk
import requests
import threading
import time
import random
from datetime import datetime
from threading import Lock
from requests.exceptions import Timeout, ConnectionError, RequestException
import json
import os

# Configure interface
ctk.set_appearance_mode("System") 
ctk.set_default_color_theme("blue")

class Discord9ChannelBot(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Discord Multi-Timer v5.2 - Professional+")
        self.geometry("1100x780")
        self.is_running = False
        self.is_paused = False
        self.log_lock = Lock()
        self.ui_lock = Lock()
        self.log_visible = True
        self.dynamic_channels = {}
        self.dynamic_counter = 0
        
        # Statistics
        self.stats = {"success": 0, "error": 0, "total_messages": 0}
        self.stats_lock = Lock()
        
        # Default cooldown (seconds)
        self.default_cooldowns = [60, 300, 300, 360, 360, 360, 600, 600, 600]

        # --- MAIN INTERFACE ---
        self.label_title = ctk.CTkLabel(self, text="DISCORD MULTI-TIMER PRO v5.2+", font=("Roboto", 22, "bold"))
        self.label_title.pack(pady=10)

        # Frame Token & Message (Compact)
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(pady=5, padx=10, fill="x")

        self.token_entry = ctk.CTkEntry(top_frame, placeholder_text="Paste User Token here...", show="*", width=400)
        self.token_entry.pack(side="left", padx=10, pady=10)

        self.message_text = ctk.CTkTextbox(top_frame, height=60, width=500)
        self.message_text.pack(side="right", padx=10, pady=10)
        self.message_text.insert("0.0", "Message content...")

        # --- GRID 9 CHANNELS ---
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=10, padx=10, fill="x")
        
        self.entries = []
        self.cooldown_entries = []
        self.timer_labels = []

        for i in range(9):
            row, col = i // 3, i % 3
            frame = ctk.CTkFrame(self.main_frame, fg_color="gray17", corner_radius=8)
            frame.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
            
            ctk.CTkLabel(frame, text=f"Channel {i+1}", font=("Roboto", 11, "bold")).pack(pady=2)
            
            id_ent = ctk.CTkEntry(frame, placeholder_text="Channel ID", height=25)
            id_ent.pack(pady=2, padx=10, fill="x")
            self.entries.append(id_ent)
            
            cool_ent = ctk.CTkEntry(frame, placeholder_text="Cooldown (sec)", height=25)
            cool_ent.insert(0, str(self.default_cooldowns[i]))
            cool_ent.pack(pady=2, padx=10, fill="x")
            self.cooldown_entries.append(cool_ent)
            
            t_lbl = ctk.CTkLabel(frame, text="⏱️ Ready", text_color="gray", font=("Roboto", 10))
            t_lbl.pack(pady=2)
            self.timer_labels.append(t_lbl)
        
        for col in range(3): self.main_frame.grid_columnconfigure(col, weight=1)

        # --- ADD DYNAMIC CHANNEL ---
        add_frame = ctk.CTkFrame(self)
        add_frame.pack(pady=5, padx=10, fill="x")
        
        ctk.CTkLabel(add_frame, text="Quick Add:", font=("Roboto", 12, "bold")).pack(side="left", padx=10)
        self.new_id = ctk.CTkEntry(add_frame, placeholder_text="New ID", width=200)
        self.new_id.pack(side="left", padx=5)
        self.new_cool = ctk.CTkEntry(add_frame, placeholder_text="Cooldown (sec)", width=100)
        self.new_cool.pack(side="left", padx=5)
        
        ctk.CTkButton(add_frame, text="+ Add Channel", width=100, fg_color="#27ae60", command=self.add_channel).pack(side="left", padx=5)

        # --- ADDED CHANNELS & LOG SIDE BY SIDE ---
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(pady=5, padx=10, fill="both", expand=True)
        
        # Left side - Added channels
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        ctk.CTkLabel(left_frame, text="Added Channels", font=("Roboto", 11, "bold")).pack()
        self.scroll_frame = ctk.CTkScrollableFrame(left_frame, height=200)
        self.scroll_frame.pack(fill="both", expand=True)

        # Right side - Log
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        ctk.CTkLabel(right_frame, text="System Log", font=("Roboto", 11, "bold")).pack()
        self.log_frame = ctk.CTkFrame(right_frame)
        self.log_frame.pack(fill="both", expand=True)
        self.log_view = ctk.CTkTextbox(self.log_frame, state="disabled", font=("Consolas", 9))
        self.log_view.pack(fill="both", expand=True)

        # --- CONTROL BUTTONS (Start, Stop, Pause, Log, Clear, Save) ---
        ctrl_frame = ctk.CTkFrame(self, fg_color="transparent")
        ctrl_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(ctrl_frame, text="▶ START", fg_color="#2ecc71", width=120, height=38, font=("Roboto", 12, "bold"), command=self.start_all)
        self.start_btn.pack(side="left", padx=5)

        self.pause_btn = ctk.CTkButton(ctrl_frame, text="⏸ PAUSE", fg_color="#f39c12", width=120, height=38, font=("Roboto", 12, "bold"), command=self.toggle_pause, state="disabled")
        self.pause_btn.pack(side="left", padx=5)

        self.stop_btn = ctk.CTkButton(ctrl_frame, text="⏹ STOP", fg_color="#e74c3c", width=120, height=38, font=("Roboto", 12, "bold"), command=self.stop_all, state="disabled")
        self.stop_btn.pack(side="left", padx=5)

        self.log_btn = ctk.CTkButton(ctrl_frame, text="👁 HIDE LOG", fg_color="#9b59b6", width=120, height=38, font=("Roboto", 12, "bold"), command=self.toggle_log)
        self.log_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(ctrl_frame, text="🗑 CLEAR LOG", fg_color="#34495e", width=110, height=38, font=("Roboto", 12, "bold"), command=self.clear_log)
        self.clear_btn.pack(side="left", padx=5)
        
        self.save_btn = ctk.CTkButton(ctrl_frame, text="💾 SAVE CONFIG", fg_color="#16a085", width=130, height=38, font=("Roboto", 12, "bold"), command=self.save_config)
        self.save_btn.pack(side="left", padx=5)

        # --- STATISTICS ---
        stats_frame = ctk.CTkFrame(self, fg_color="gray17")
        stats_frame.pack(pady=5, padx=10, fill="x")
        
        # Divide statistics into separate labels with different colors
        stats_inner = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_inner.pack(pady=5, padx=10)
        
        self.stats_success_label = ctk.CTkLabel(stats_inner, text="✅ Success: 0", font=("Roboto", 11, "bold"), text_color="#2ecc71")
        self.stats_success_label.pack(side="left", padx=15)
        
        self.stats_error_label = ctk.CTkLabel(stats_inner, text="❌ Error: 0", font=("Roboto", 11, "bold"), text_color="#e74c3c")
        self.stats_error_label.pack(side="left", padx=15)
        
        self.stats_total_label = ctk.CTkLabel(stats_inner, text="📤 Total: 0", font=("Roboto", 11, "bold"), text_color="#3498db")
        self.stats_total_label.pack(side="left", padx=15)

        self.log("✅ Application started successfully - v5.2+")
        
        # Auto load previous config if exists
        self.after(500, self.load_config)
        
        # Auto load previous config if exists
        self.after(500, self.load_config)

    def toggle_log(self):
        if self.log_visible:
            right_frame = self.log_frame.master
            right_frame.pack_forget()
            self.log_btn.configure(text="👁 SHOW LOG")
        else:
            right_frame = self.log_frame.master
            right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
            self.log_btn.configure(text="👁 HIDE LOG")
        self.log_visible = not self.log_visible

    def log(self, message):
        with self.log_lock:
            self.log_view.configure(state="normal")
            self.log_view.insert("end", f"[{datetime.now().strftime('%H:%M:%S')}] {message}\n")
            self.log_view.see("end")
            self.log_view.configure(state="disabled")
    
    def clear_log(self):
        with self.log_lock:
            self.log_view.configure(state="normal")
            self.log_view.delete("0.0", "end")
            self.log_view.configure(state="disabled")
        self.log("🗑 Log cleared")
    
    def update_stats(self):
        with self.stats_lock:
            with self.ui_lock:
                self.stats_success_label.configure(text=f"✅ Success: {self.stats['success']}")
                self.stats_error_label.configure(text=f"❌ Error: {self.stats['error']}")
                self.stats_total_label.configure(text=f"📤 Total: {self.stats['total_messages']}")

    def add_channel(self):
        cid, cool = self.new_id.get().strip(), self.new_cool.get().strip()
        
        # Better validation
        if not cid:
            self.log("❌ Error: Channel ID cannot be empty!")
            return
        if not cid.isdigit():
            self.log("❌ Error: Channel ID must be numeric!")
            return
        if not cool or not cool.isdigit() or int(cool) <= 0:
            self.log("❌ Error: Cooldown must be a positive number!")
            return
        
        idx = 100 + self.dynamic_counter
        self.dynamic_counter += 1
        
        f = ctk.CTkFrame(self.scroll_frame)
        f.pack(fill="x", pady=2)
        
        lbl = ctk.CTkLabel(f, text=f"Channel +{self.dynamic_counter} (ID: {cid}) - Cooldown: {cool}s", width=450, anchor="w")
        lbl.pack(side="left", padx=10)
        
        t_lbl = ctk.CTkLabel(f, text="⏱️ Waiting", text_color="gray", width=100)
        t_lbl.pack(side="left", padx=10)
        
        ctk.CTkButton(f, text="Remove", width=60, fg_color="#c0392b", command=lambda: self.remove_ch(idx, f)).pack(side="right", padx=5)
        
        self.dynamic_channels[idx] = {"id": cid, "cool": int(cool), "timer_label": t_lbl}
        self.new_id.delete(0, 'end')
        self.new_cool.delete(0, 'end')
        self.log(f"✅ Channel added successfully: ID {cid} - Cooldown {cool}s")

    def remove_ch(self, idx, frame):
        frame.destroy()
        if idx in self.dynamic_channels:
            del self.dynamic_channels[idx]
            self.log(f"✅ Channel removed successfully")

    def disable_inputs(self, disabled=True):
        state = "disabled" if disabled else "normal"
        self.token_entry.configure(state=state)
        self.message_text.configure(state=state)
        self.new_id.configure(state=state)
        self.new_cool.configure(state=state)
        for entry in self.entries:
            entry.configure(state=state)
        for entry in self.cooldown_entries:
            entry.configure(state=state)

    def validate_inputs(self):
        token = self.token_entry.get().strip()
        msg = self.message_text.get("0.0", "end").strip()
        
        if not token:
            self.log("❌ Error: Token not entered!")
            return False
        if not msg or msg == "Message content...":
            self.log("❌ Error: Message cannot be empty!")
            return False
        
        has_channels = False
        for i in range(9):
            if self.entries[i].get().strip():
                has_channels = True
                break
        
        if not has_channels and not self.dynamic_channels:
            self.log("❌ Error: Must add at least 1 channel!")
            return False
        
        return True

    def start_all(self):
        if not self.validate_inputs():
            return
        
        token = self.token_entry.get().strip()
        self.is_running = True
        self.is_paused = False
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")
        self.stop_btn.configure(state="normal")
        self.disable_inputs(True)
        
        # Reset stats
        with self.stats_lock:
            self.stats = {"success": 0, "error": 0, "total_messages": 0}
        self.update_stats()
        
        self.log("🚀 System started...")
        
        # Run 9 fixed channels
        for i in range(9):
            cid, cool = self.entries[i].get().strip(), self.cooldown_entries[i].get().strip()
            if cid and cool.isdigit() and int(cool) > 0:
                threading.Thread(target=self.worker, args=(i, cid, int(cool), token, f"CH {i+1}"), daemon=True).start()
        
        # Run dynamic channels
        for idx, data in self.dynamic_channels.items():
            threading.Thread(target=self.worker, args=(idx, data['id'], data['cool'], token, f"Channel +{idx-99}"), daemon=True).start()

    def toggle_pause(self):
        if self.is_running:
            self.is_paused = not self.is_paused
            if self.is_paused:
                self.pause_btn.configure(text="▶ RESUME")
                self.log("⏸ System paused")
            else:
                self.pause_btn.configure(text="⏸ PAUSE")
                self.log("▶ System resumed")

    def stop_all(self):
        self.is_running = False
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")
        self.pause_btn.configure(text="⏸ PAUSE")
        self.stop_btn.configure(state="disabled")
        self.disable_inputs(False)
        self.log("⏹ System stopped")

    def worker(self, idx, cid, cool, token, name):
        url = f"https://discord.com/api/v10/channels/{cid}/messages"
        headers = {"Authorization": token, "Content-Type": "application/json"}
        retry_count = 0
        max_retries = 3
        
        while self.is_running:
            # Xử lý pause
            while self.is_paused and self.is_running:
                time.sleep(0.5)
            
            if not self.is_running:
                break
            
            try:
                msg = self.message_text.get("0.0", "end").strip()
                res = requests.post(url, json={"content": msg}, headers=headers, timeout=10)
                
                if res.status_code == 200:
                    self.log(f"✅ {name}: Message sent successfully")
                    with self.stats_lock:
                        self.stats['success'] += 1
                        self.stats['total_messages'] += 1
                    self.update_stats()
                    retry_count = 0
                    
                elif res.status_code == 429:
                    wait = int(res.headers.get("Retry-After", 5))
                    self.log(f"⏳ {name}: Rate Limited! Waiting {wait}s")
                    time.sleep(wait)
                    
                elif res.status_code == 401:
                    self.log(f"❌ {name}: Invalid or expired token!")
                    with self.stats_lock:
                        self.stats['error'] += 1
                    self.update_stats()
                    self.is_running = False
                    break
                    
                elif res.status_code == 403:
                    self.log(f"❌ {name}: No permission to send messages (Forbidden)")
                    with self.stats_lock:
                        self.stats['error'] += 1
                    self.update_stats()
                    self.is_running = False
                    break
                    
                elif res.status_code == 404:
                    self.log(f"❌ {name}: Channel ID does not exist")
                    with self.stats_lock:
                        self.stats['error'] += 1
                    self.update_stats()
                    self.is_running = False
                    break
                    
                else:
                    self.log(f"⚠️ {name}: HTTP Error {res.status_code}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        self.log(f"❌ {name}: Exceeded max retries ({max_retries}x)")
                        with self.stats_lock:
                            self.stats['error'] += 1
                        self.update_stats()
                        break
                    time.sleep(2 * retry_count)
                    
            except Timeout:
                self.log(f"⚠️ {name}: Timeout - Connection took too long")
                retry_count += 1
            except ConnectionError:
                self.log(f"⚠️ {name}: Network error - Auto-reconnecting...")
                retry_count += 1
                time.sleep(3)
            except Exception as e:
                self.log(f"❗ {name}: {str(e)}")
                retry_count += 1

            # Đếm ngược
            rem = cool + random.randint(1, 5)
            while rem > 0 and self.is_running:
                # Skip khi pause
                while self.is_paused and self.is_running:
                    time.sleep(0.5)
                
                if not self.is_running:
                    break
                
                m, s = divmod(rem, 60)
                txt = f"⏱️ {m:02d}:{s:02d}"
                
                with self.ui_lock:
                    try:
                        if idx < 9:
                            self.timer_labels[idx].configure(text=txt, text_color="#3498db")
                        elif idx in self.dynamic_channels:
                            self.dynamic_channels[idx]['timer_label'].configure(text=txt, text_color="#3498db")
                    except:
                        pass
                
                time.sleep(1)
                rem -= 1
            
            if not self.is_running:
                break
        
        # Update stopped status
        with self.ui_lock:
            try:
                if idx < 9:
                    self.timer_labels[idx].configure(text="🛑 Stopped", text_color="red")
                elif idx in self.dynamic_channels:
                    self.dynamic_channels[idx]['timer_label'].configure(text="🛑 Stopped", text_color="red")
            except:
                pass
    
    def save_config(self):
        """Save current configuration"""
        config = {
            "token": self.token_entry.get().strip(),
            "message": self.message_text.get("0.0", "end").strip(),
            "channels_9": [],
            "channels_dynamic": {}
        }
        
        # Save 9 channels
        for i in range(9):
            cid = self.entries[i].get().strip()
            cool = self.cooldown_entries[i].get().strip()
            if cid and cool:
                config["channels_9"].append({"id": cid, "cool": cool})
        
        # Save dynamic channels
        for idx, data in self.dynamic_channels.items():
            config["channels_dynamic"][str(idx)] = {"id": data["id"], "cool": data["cool"]}
        
        try:
            with open("discord_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.log("💾 Configuration saved to: discord_config.json")
        except Exception as e:
            self.log(f"❌ Error saving configuration: {str(e)}")
    
    def load_config(self):
        """Auto load configuration from file if exists"""
        try:
            if not os.path.exists("discord_config.json"):
                return
            
            with open("discord_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Load token
            token = config.get("token", "").strip()
            if token:
                self.token_entry.delete(0, "end")
                self.token_entry.insert(0, token)
            
            # Load message
            message = config.get("message", "").strip()
            if message:
                self.message_text.delete("0.0", "end")
                self.message_text.insert("0.0", message)
            
            # Load 9 channels
            channels_9 = config.get("channels_9", [])
            for i, ch in enumerate(channels_9):
                if i < 9:
                    self.entries[i].delete(0, "end")
                    self.entries[i].insert(0, ch.get("id", ""))
                    self.cooldown_entries[i].delete(0, "end")
                    self.cooldown_entries[i].insert(0, str(ch.get("cool", self.default_cooldowns[i])))
            
            # Load dynamic channels
            channels_dynamic = config.get("channels_dynamic", {})
            for idx_str, data in channels_dynamic.items():
                try:
                    cid = data.get("id", "").strip()
                    cool = str(data.get("cool", ""))
                    
                    if cid and cool.isdigit():
                        # Recreate dynamic channel
                        self.new_id.delete(0, "end")
                        self.new_id.insert(0, cid)
                        self.new_cool.delete(0, "end")
                        self.new_cool.insert(0, cool)
                        self.add_channel()
                except:
                    continue
            
            self.log(f"✅ Configuration loaded from: discord_config.json")
        except Exception as e:
            self.log(f"⚠️ Could not load configuration: {str(e)}")

if __name__ == "__main__":
    app = Discord9ChannelBot()
    app.mainloop()