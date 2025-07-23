import tkinter as tk
from tkinter import Toplevel, Listbox, messagebox, Frame, Label, Entry, Button, Menu, filedialog
import pygetwindow as gw
import pyautogui
import time
import json
from pynput import keyboard
from datetime import datetime, timedelta

class AdvancedAutoClicker:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Automation Tool")
        self.root.geometry("450x550")

        # --- State Variables ---
        self.target_window = None
        self.scheduled_action_id = None
        self.key_listener = None

        # --- NEW: Menu Bar for Save/Load ---
        self.create_menu()

        # --- GUI WIDGETS (Organized into Frames) ---

        # Frame 1: Window Selection
        win_frame = Frame(root, bd=2, relief=tk.RIDGE)
        win_frame.pack(pady=5, padx=10, fill=tk.X)
        Label(win_frame, text="Step 1: Select Target Window", font=('Helvetica', 10, 'bold')).pack()
        self.select_window_btn = Button(win_frame, text="Select Chrome Window", command=self.select_window_popup)
        self.select_window_btn.pack(pady=5, padx=10, fill=tk.X)

        # Frame 2: Location Selection & Adjustment
        loc_frame = Frame(root, bd=2, relief=tk.RIDGE)
        loc_frame.pack(pady=5, padx=10, fill=tk.X)
        Label(loc_frame, text="Step 2: Select Action Location", font=('Helvetica', 10, 'bold')).pack()
        self.select_location_btn = Button(loc_frame, text="Select Location with Mouse (Press 'Esc')", command=self.start_location_selection)
        self.select_location_btn.pack(pady=5, padx=10, fill=tk.X)
        
        coord_frame = Frame(loc_frame)
        coord_frame.pack(pady=5)
        Label(coord_frame, text="Coords (X, Y):").pack(side=tk.LEFT, padx=5)
        self.coord_x_entry = Entry(coord_frame, width=6)
        self.coord_x_entry.pack(side=tk.LEFT)
        self.coord_y_entry = Entry(coord_frame, width=6)
        self.coord_y_entry.pack(side=tk.LEFT, padx=5)
        # NEW: Test Location Button
        self.test_loc_btn = Button(coord_frame, text="Test", command=self.test_location)
        self.test_loc_btn.pack(side=tk.LEFT)

        # Frame 3: Action Configuration
        action_frame = Frame(root, bd=2, relief=tk.RIDGE)
        action_frame.pack(pady=5, padx=10, fill=tk.X)
        Label(action_frame, text="Step 3: Configure Action", font=('Helvetica', 10, 'bold')).pack()
        
        # NEW: Multi-click settings
        clicks_frame = Frame(action_frame)
        clicks_frame.pack(fill=tk.X, padx=10, pady=2)
        Label(clicks_frame, text="Number of Clicks:").pack(side=tk.LEFT)
        self.clicks_entry = Entry(clicks_frame, width=5)
        self.clicks_entry.insert(0, "1")
        self.clicks_entry.pack(side=tk.LEFT, padx=5)
        Label(clicks_frame, text="Interval (s):").pack(side=tk.LEFT)
        self.interval_entry = Entry(clicks_frame, width=5)
        self.interval_entry.insert(0, "0.1")
        self.interval_entry.pack(side=tk.LEFT, padx=5)

        # NEW: Text typing settings
        type_frame = Frame(action_frame)
        type_frame.pack(fill=tk.X, padx=10, pady=(2, 10))
        Label(type_frame, text="Text to Type (optional):").pack(side=tk.LEFT)
        self.text_entry = Entry(type_frame)
        self.text_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        
        # Frame 4: Timing and Controls
        timing_frame = Frame(root, bd=2, relief=tk.RIDGE)
        timing_frame.pack(pady=5, padx=10, fill=tk.X)
        Label(timing_frame, text="Step 4: Schedule and Execute", font=('Helvetica', 10, 'bold')).pack()
        
        absolute_time_frame = Frame(timing_frame)
        absolute_time_frame.pack(pady=5, fill=tk.X, padx=10)
        Label(absolute_time_frame, text="Execute at (HH:MM:SS):").pack(side=tk.LEFT)
        self.absolute_time_entry = Entry(absolute_time_frame)
        self.absolute_time_entry.pack(side=tk.LEFT, padx=5, expand=True, fill=tk.X)
        self.set_default_absolute_time()
        
        # NEW: Control Buttons (Start/Stop)
        control_frame = Frame(root)
        control_frame.pack(pady=10, padx=10, fill=tk.X)
        self.start_btn = Button(control_frame, text="Schedule Action", command=self.schedule_action, bg="#4CAF50", fg="white", font=('Helvetica', 10, 'bold'))
        self.start_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.stop_btn = Button(control_frame, text="Stop Action", command=self.stop_action, bg="#f44336", fg="white", font=('Helvetica', 10, 'bold'))
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5, padx=(10, 0))

        # Status Label
        self.status_label = Label(root, text="Status: Ready. Load a profile or configure a new action.", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)

    # --- Feature Implementations ---

    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)
        file_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save Profile", command=self.save_profile)
        file_menu.add_command(label="Load Profile", command=self.load_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

    def save_profile(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Profile As"
        )
        if not filepath: return
        
        profile_data = {
            "target_window_title": self.target_window.title if self.target_window else "",
            "coord_x": self.coord_x_entry.get(),
            "coord_y": self.coord_y_entry.get(),
            "num_clicks": self.clicks_entry.get(),
            "interval": self.interval_entry.get(),
            "text_to_type": self.text_entry.get(),
            "exec_time": self.absolute_time_entry.get()
        }
        try:
            with open(filepath, 'w') as f:
                json.dump(profile_data, f, indent=4)
            self.update_status(f"Profile saved to {filepath}")
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save profile: {e}")

    def load_profile(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Load Profile"
        )
        if not filepath: return

        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            # Populate fields
            self.coord_x_entry.delete(0, tk.END); self.coord_x_entry.insert(0, data.get("coord_x", ""))
            self.coord_y_entry.delete(0, tk.END); self.coord_y_entry.insert(0, data.get("coord_y", ""))
            self.clicks_entry.delete(0, tk.END); self.clicks_entry.insert(0, data.get("num_clicks", "1"))
            self.interval_entry.delete(0, tk.END); self.interval_entry.insert(0, data.get("interval", "0.1"))
            self.text_entry.delete(0, tk.END); self.text_entry.insert(0, data.get("text_to_type", ""))
            self.absolute_time_entry.delete(0, tk.END); self.absolute_time_entry.insert(0, data.get("exec_time", ""))

            # Find the window by title
            title_to_find = data.get("target_window_title")
            if title_to_find:
                found_window = gw.getWindowsWithTitle(title_to_find)
                if found_window:
                    self.target_window = found_window[0]
                    self.update_status(f"Profile loaded. Window '{title_to_find[:30]}...' found and set.")
                else:
                    self.target_window = None
                    messagebox.showwarning("Window Not Found", f"Could not find an open window with title:\n'{title_to_find}'\nPlease select it manually.")
                    self.update_status(f"Profile loaded, but window not found. Please select manually.")
            else:
                self.update_status("Profile loaded. Select a window.")

        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load profile: {e}")
    
    def test_location(self):
        try:
            x = int(self.coord_x_entry.get())
            y = int(self.coord_y_entry.get())
            if not self.target_window:
                messagebox.showerror("Error", "Select a target window first to test location.")
                return

            win_x, win_y = self.target_window.topleft
            abs_x = win_x + x
            abs_y = win_y + y

            # Create a temporary, semi-transparent red square
            preview = Toplevel(self.root)
            preview.geometry(f'20x20+{abs_x-10}+{abs_y-10}')
            preview.overrideredirect(True) # No title bar
            preview.attributes('-topmost', True)
            preview.attributes('-alpha', 0.6)
            preview.config(bg='red')
            # Destroy the preview window after 600ms
            self.root.after(600, preview.destroy)

        except (ValueError, gw.PyGetWindowException):
            messagebox.showerror("Error", "Invalid coordinates or window closed.")

    def stop_action(self):
        if self.scheduled_action_id:
            self.root.after_cancel(self.scheduled_action_id)
            self.scheduled_action_id = None
            self.update_status("Action canceled by user.")
        else:
            self.update_status("No scheduled action to stop.")
    
    def schedule_action(self):
        # 1. Validate inputs
        try:
            click_location = (int(self.coord_x_entry.get()), int(self.coord_y_entry.get()))
            num_clicks = int(self.clicks_entry.get())
            interval = float(self.interval_entry.get())
            text_to_type = self.text_entry.get()
            absolute_time_str = self.absolute_time_entry.get()
            
            if not self.target_window:
                messagebox.showerror("Error", "Please select a target window.")
                return
            if num_clicks <= 0 or interval < 0:
                raise ValueError("Clicks and interval must be positive numbers.")

        except (ValueError, tk.TclError):
            messagebox.showerror("Input Error", "Invalid input. Check coordinates, clicks, and interval.")
            return

        # 2. Calculate delay
        try:
            now = datetime.now()
            target_time_obj = datetime.strptime(absolute_time_str, "%H:%M:%S").time()
            target_dt = now.replace(hour=target_time_obj.hour, minute=target_time_obj.minute, second=target_time_obj.second, microsecond=0)
            if target_dt < now: target_dt += timedelta(days=1)
            delay_seconds = (target_dt - now).total_seconds()
            self.update_status(f"Action scheduled for {target_dt.strftime('%Y-%m-%d %H:%M:%S')}")

        except ValueError:
            messagebox.showerror("Time Error", "Time format is invalid. Use HH:MM:SS.")
            return

        # 3. Schedule the action
        delay_ms = int(delay_seconds * 1000)
        action_params = (click_location, num_clicks, interval, text_to_type)
        self.scheduled_action_id = self.root.after(delay_ms, lambda: self.perform_action(*action_params))
        
    def perform_action(self, click_location, num_clicks, interval, text_to_type):
        self.update_status("Time reached. Performing action...")
        try:
            if self.target_window not in gw.getAllWindows(): raise gw.PyGetWindowException
            self.target_window.activate()
            time.sleep(0.2)
            win_x, win_y = self.target_window.topleft
            abs_x = win_x + click_location[0]
            abs_y = win_y + click_location[1]

            # Perform clicks
            for i in range(num_clicks):
                pyautogui.click(abs_x, abs_y)
                self.update_status(f"Click {i+1}/{num_clicks} performed.")
                if i < num_clicks - 1:
                    time.sleep(interval)
            
            # Perform typing
            if text_to_type:
                self.update_status("Typing text...")
                pyautogui.typewrite(text_to_type, interval=0.05)

            self.update_status("Action completed successfully! Ready for next task.")
            self.set_default_absolute_time() # Reset default time
            self.scheduled_action_id = None # Clear the completed task ID

        except gw.PyGetWindowException:
            messagebox.showerror("Error", "Target window was closed.")
            self.update_status("Error: Target window closed.")
        except Exception as e:
            messagebox.showerror("Error", f"An unexpected error occurred: {e}")

    # --- Helper & Original Functions (slightly modified) ---
    
    def set_default_absolute_time(self):
        future_time = datetime.now() + timedelta(minutes=2)
        self.absolute_time_entry.delete(0, tk.END)
        self.absolute_time_entry.insert(0, future_time.strftime("%H:%M:%S"))

    def update_status(self, message):
        self.status_label.config(text=f"Status: {message}")
        self.root.update_idletasks()
    
    def on_key_press(self, key):
        if key == keyboard.Key.esc:
            mouse_x, mouse_y = pyautogui.position()
            if self.target_window and self.target_window.isActive:
                win_x, win_y = self.target_window.topleft
                rel_x, rel_y = mouse_x - win_x, mouse_y - win_y
                self.coord_x_entry.delete(0, tk.END); self.coord_x_entry.insert(0, str(rel_x))
                self.coord_y_entry.delete(0, tk.END); self.coord_y_entry.insert(0, str(rel_y))
                self.update_status(f"Location saved at ({rel_x}, {rel_y}). Test it or adjust manually.")
            else: self.update_status("Failed to get location. Window not active.")
            return False # Stop listener

    def select_window_popup(self):
        # This function remains largely the same as before
        ... 

    def start_location_selection(self):
        # This function remains largely the same as before
        ...

# --- Boilerplate code for popup and key listener from previous version ---
    def select_window_popup(self):
        self.update_status("Searching for Chrome windows...")
        chrome_windows = gw.getWindowsWithTitle('Chrome')
        if not chrome_windows:
            messagebox.showerror("Error", "No Chrome windows found!")
            self.update_status("Error: No Chrome windows found.")
            return
        popup = Toplevel(self.root)
        popup.title("Select a Window")
        listbox = Listbox(popup, width=60, height=10)
        listbox.pack(padx=10, pady=10)
        for i, win in enumerate(chrome_windows): listbox.insert(i, win.title if win.title else "[No Title]")
        def on_select():
            selected_indices = listbox.curselection()
            if not selected_indices: return
            self.target_window = chrome_windows[selected_indices[0]]
            self.update_status(f"Window selected: '{self.target_window.title[:40]}...'")
            popup.destroy()
        Button(popup, text="Select", command=on_select).pack(pady=5)
        
    def start_location_selection(self):
        if not self.target_window:
            messagebox.showerror("Error", "Please select a Chrome window first!")
            return
        self.update_status("Move mouse to target location and press 'Esc' to confirm.")
        try: self.target_window.activate()
        except gw.PyGetWindowException:
            messagebox.showerror("Error", "The selected window has been closed."); self.target_window = None; self.update_status("Window lost.")
            return
        if self.key_listener is None or not self.key_listener.is_alive():
            self.key_listener = keyboard.Listener(on_press=self.on_key_press); self.key_listener.start()

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedAutoClicker(root)
    root.mainloop()
