import time
import json
from pynput import mouse, keyboard
from pynput.mouse import Button, Controller as MouseController
from pynput.keyboard import Controller as KeyboardController

class ActionRecorder:
    def __init__(self):
        self.actions = []
        self.start_time = None
        self.mouse_listener = None
        self.keyboard_listener = None
        self.recording = False
    
    def on_move(self, x, y):
        if self.recording:
            current_time = time.time() - self.start_time
            self.actions.append({
                'type': 'move',
                'x': x,
                'y': y,
                'time': current_time
            })
    
    def on_click(self, x, y, button, pressed):
        if self.recording:
            current_time = time.time() - self.start_time
            self.actions.append({
                'type': 'click',
                'x': x,
                'y': y,
                'button': str(button),
                'pressed': pressed,
                'time': current_time
            })
    
    def on_press(self, key):
        if self.recording:
            current_time = time.time() - self.start_time
            try:
                char = key.char
            except AttributeError:
                char = str(key)
            
            self.actions.append({
                'type': 'key_press',
                'key': char,
                'time': current_time
            })
    
    def start_recording(self):
        self.actions = []
        self.start_time = time.time()
        self.recording = True
        
        # Start listeners
        self.mouse_listener = mouse.Listener(
            on_move=self.on_move,
            on_click=self.on_click)
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_press)
        
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        print("Recording started... Press ESC to stop.")
    
    def stop_recording(self):
        self.recording = False
        if self.mouse_listener:
            self.mouse_listener.stop()
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        print("Recording stopped. Total actions recorded:", len(self.actions))
    
    def save_recording(self, filename):
        with open(filename, 'w') as f:
            json.dump(self.actions, f)
        print(f"Recording saved to {filename}")
    
    def load_recording(self, filename):
        with open(filename, 'r') as f:
            self.actions = json.load(f)
        print(f"Recording loaded from {filename}. Total actions:", len(self.actions))
    
    def replay(self, speed=1.0):
        if not self.actions:
            print("No actions to replay")
            return
        
        mouse_ctrl = MouseController()
        keyboard_ctrl = KeyboardController()
        
        print(f"Replaying {len(self.actions)} actions...")
        
        start_time = time.time()
        last_action_time = 0
        
        for action in self.actions:
            # Wait until it's time for this action
            while True:
                elapsed = (time.time() - start_time) * speed
                if elapsed >= action['time']:
                    break
                time.sleep(0.001)
            
            # Execute the action
            if action['type'] == 'move':
                mouse_ctrl.position = (action['x'], action['y'])
            elif action['type'] == 'click':
                button = Button.left if action['button'] == 'Button.left' else Button.right
                if action['pressed']:
                    mouse_ctrl.press(button)
                else:
                    mouse_ctrl.release(button)
            elif action['type'] == 'key_press':
                try:
                    # Handle special keys
                    if action['key'].startswith('Key.'):
                        key_name = action['key'].split('.')[1]
                        key = getattr(keyboard.Key, key_name)
                        keyboard_ctrl.press(key)
                        keyboard_ctrl.release(key)
                    else:
                        keyboard_ctrl.press(action['key'])
                        keyboard_ctrl.release(action['key'])
                except Exception as e:
                    print(f"Failed to press key: {action['key']}, error: {e}")
        
        print("Replay completed")

def main():
    recorder = ActionRecorder()
    
    while True:
        print("\nMenu:")
        print("1. Start recording")
        print("2. Stop recording")
        print("3. Save recording to file")
        print("4. Load recording from file")
        print("5. Replay recording")
        print("6. Exit")
        
        choice = input("Enter your choice (1-6): ")
        
        if choice == '1':
            recorder.start_recording()
        elif choice == '2':
            recorder.stop_recording()
        elif choice == '3':
            filename = input("Enter filename to save: ")
            recorder.save_recording(filename)
        elif choice == '4':
            filename = input("Enter filename to load: ")
            recorder.load_recording(filename)
        elif choice == '5':
            speed = float(input("Enter replay speed (1.0 = normal speed): ") or "1.0")
            recorder.replay(speed)
        elif choice == '6':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()