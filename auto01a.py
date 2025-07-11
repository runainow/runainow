import tkinter as tk
from tkinter import messagebox
import pyautogui
import time
import datetime
import threading

# Set pyautogui to fail-safe mode (move mouse to upper-left corner to stop)
pyautogui.FAILSAFE = True

class AutoClickerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Auto Clicker")
        self.root.geometry("400x450")

        # Variables
        self.click_position_1 = None
        self.click_position_2 = None
        self.target_time = None
        self.running = False
        self.current_position_setting = None
        self.click_delay = tk.DoubleVar(value=1.0)  # Default delay of 1 second

        # GUI Elements
        tk.Label(root, text="Set Click Time (HH:MM:SS, 24-hour format):").pack(pady=5)
        self.time_entry = tk.Entry(root)
        self.time_entry.pack(pady=5)

        tk.Label(root, text="Delay between clicks (seconds):").pack(pady=5)
        self.delay_entry = tk.Entry(root, textvariable=self.click_delay)
        self.delay_entry.pack(pady=5)

        tk.Button(root, text="Set Time to Now + 30 Seconds & Start", command=self.set_time_plus_thirty_and_start).pack(pady=5)
        tk.Button(root, text="Set Time to Now + 1 Minute & Start", command=self.set_time_plus_one_and_start).pack(pady=5)
        tk.Button(root, text="Set Time to Now + 2 Minutes", command=self.set_time_plus_two_minutes).pack(pady=5)
        
        tk.Button(root, text="Set Click Position 1", command=lambda: self.set_position(1)).pack(pady=5)
        self.position_label_1 = tk.Label(root, text="Position 1: Not set")
        self.position_label_1.pack(pady=5)
        
        tk.Button(root, text="Set Click Position 2", command=lambda: self.set_position(2)).pack(pady=5)
        self.position_label_2 = tk.Label(root, text="Position 2: Not set")
        self.position_label_2.pack(pady=5)

        tk.Button(root, text="Start Auto Clicker", command=self.start_clicker).pack(pady=5)
        tk.Button(root, text="Stop Auto Clicker", command=self.stop_clicker).pack(pady=5)

        self.status_label = tk.Label(root, text="Status: Idle")
        self.status_label.pack(pady=10)

    def set_time_plus_thirty_and_start(self):
        # Set time entry to current time + 30 seconds and start clicker
        if self.running:
            messagebox.showwarning("Warning", "Auto clicker is already running!")
            return

        if not self.click_position_1 and not self.click_position_2:
            messagebox.showerror("Error", "Please set at least one click position!")
            return

        current_time = datetime.datetime.now()
        self.target_time = current_time + datetime.timedelta(seconds=30)
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, self.target_time.strftime("%H:%M:%S"))
        self.status_label.config(text="Status: Time set to now + 30 seconds, starting...")
        
        self.running = True
        threading.Thread(target=self.click_at_time, daemon=True).start()

    def set_time_plus_one_and_start(self):
        # Set time entry to current time + 1 minute and start clicker
        if self.running:
            messagebox.showwarning("Warning", "Auto clicker is already running!")
            return

        if not self.click_position_1 and not self.click_position_2:
            messagebox.showerror("Error", "Please set at least one click position!")
            return

        current_time = datetime.datetime.now()
        self.target_time = current_time + datetime.timedelta(minutes=1)
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, self.target_time.strftime("%H:%M:%S"))
        self.status_label.config(text="Status: Time set to now + 1 minute, starting...")
        
        self.running = True
        threading.Thread(target=self.click_at_time, daemon=True).start()

    def set_time_plus_two_minutes(self):
        # Set time entry to current time + 2 minutes
        current_time = datetime.datetime.now()
        target_time = current_time + datetime.timedelta(minutes=2)
        self.time_entry.delete(0, tk.END)
        self.time_entry.insert(0, target_time.strftime("%H:%M:%S"))
        self.status_label.config(text="Status: Time set to now + 2 minutes")

    def set_position(self, position_number):
        self.current_position_setting = position_number
        self.status_label.config(text=f"Status: Move mouse to desired position {position_number} and press Enter")
        self.root.bind('<Return>', self.capture_position)
        self.root.focus_set()

    def capture_position(self, event):
        position = pyautogui.position()
        if self.current_position_setting == 1:
            self.click_position_1 = position
            self.position_label_1.config(text=f"Position 1: ({position[0]}, {position[1]})")
        elif self.current_position_setting == 2:
            self.click_position_2 = position
            self.position_label_2.config(text=f"Position 2: ({position[0]}, {position[1]})")
        self.status_label.config(text=f"Status: Position {self.current_position_setting} set")
        self.root.unbind('<Return>')
        self.current_position_setting = None

    def start_clicker(self):
        if self.running:
            messagebox.showwarning("Warning", "Auto clicker is already running!")
            return

        if not self.click_position_1 and not self.click_position_2:
            messagebox.showerror("Error", "Please set at least one click position!")
            return

        time_str = self.time_entry.get()
        try:
            self.target_time = datetime.datetime.strptime(time_str, "%H:%M:%S").replace(
                year=datetime.datetime.now().year,
                month=datetime.datetime.now().month,
                day=datetime.datetime.now().day
            )
            if self.target_time < datetime.datetime.now():
                self.target_time = self.target_time + datetime.timedelta(days=1)
        except ValueError:
            messagebox.showerror("Error", "Invalid time format! Use HH:MM:SS (24-hour)")
            return

        try:
            delay = self.click_delay.get()
            if delay < 0:
                messagebox.showerror("Error", "Delay must be non-negative!")
                return
        except tk.TclError:
            messagebox.showerror("Error", "Invalid delay format! Please enter a number (e.g., 1.0)")
            return

        self.running = True
        self.status_label.config(text="Status: Waiting for target time...")
        threading.Thread(target=self.click_at_time, daemon=True).start()

    def click_at_time(self):
        while self.running:
            current_time = datetime.datetime.now()
            if current_time >= self.target_time:
                if self.click_position_1:
                    pyautogui.click(self.click_position_1[0], self.click_position_1[1])
                if self.click_position_2:
                    time.sleep(self.click_delay.get())  # Use user-defined delay
                    pyautogui.click(self.click_position_2[0], self.click_position_2[1])
                self.status_label.config(text="Status: Clicked at target time!")
                self.running = False
                break
            time.sleep(1)

    def stop_clicker(self):
        self.running = False
        self.status_label.config(text="Status: Stopped")

if __name__ == "__main__":
    root = tk.Tk()
    app = AutoClickerApp(root)
    root.mainloop()