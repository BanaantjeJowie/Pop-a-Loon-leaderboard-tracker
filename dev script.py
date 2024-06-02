import pyautogui
import time
import keyboard
import pytesseract
from PIL import Image
import os
import tkinter as tk
from threading import Thread

# Configure Tesseract path (change this path to where Tesseract is installed on your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Balloon Popper Script")
        self.geometry("400x300")

        self.message_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.message_label.pack(pady=10)

        self.timer_label = tk.Label(self, text="", font=("Helvetica", 12))
        self.timer_label.pack(pady=10)

        self.stop_button = tk.Button(self, text="Stop Script", command=self.stop_script, font=("Helvetica", 12))
        self.stop_button.pack(pady=10)

        self.script_running = True

    def update_message(self, message):
        self.message_label.config(text=message)
        self.update_idletasks()

    def update_timer(self, timer):
        self.timer_label.config(text=timer)
        self.update_idletasks()

    def stop_script(self):
        self.script_running = False

# Function to type text with a specified interval between each character
def type_text(text, interval=0.05):
    for char in text:
        pyautogui.typewrite(char)
        time.sleep(interval)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')

# Function to capture a screenshot of a specified region and extract text from it
def capture_and_read_text(region):
    app.update_message("Capturing screenshot in 5 seconds...")
    for i in range(5, 0, -1):
        app.update_timer(f"{i} seconds...")
        time.sleep(1)
    app.update_message("Capturing screenshot now!")
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save('captured_text.png')
    text = pytesseract.image_to_string(Image.open('captured_text.png'))
    return text

# Function to process the captured text and extract scores
def process_text(text):
    lines = text.strip().split('\n')
    scores = {}
    for line in lines:
        if not line.strip():
            continue
        try:
            username, score = line.rsplit(' ', 1)
            score = int(score)
            scores[username] = score
        except ValueError:
            continue
    return scores

# Main function to run the script
def main():
    text_to_type = "/pop-a-loon"
    region = (1303, 564, 194, 272)  # Replace with the actual region coordinates of the screenshot.

    previous_scores = {}

    # Delay before starting the script
    app.update_message("Starting script in 5 seconds...")
    for i in range(5, 0, -1):
        app.update_timer(f"{i} seconds...")
        time.sleep(1)
    app.update_message("Script starting now!")

    try:
        while app.script_running:
            if keyboard.is_pressed('q'):  # Check if the 'q' key is pressed to stop the script
                app.update_message("Script stopped by user.")
                break

            type_text(text_to_type)  # Type the initial text command

            # Capture and process text
            captured_text = capture_and_read_text(region)
            current_scores = process_text(captured_text)

            # Calculate increments and type the results
            for username, current_score in current_scores.items():
                previous_score = previous_scores.get(username, None)
                if previous_score is None:
                    previous_scores[username] = current_score
                    continue  # Skip printing for the first entry
                increment = current_score - previous_score
                if increment > 0:
                    result_text = f"{username} popped {increment} Balloons in 10 minutes."
                    type_text(result_text)
                previous_scores[username] = current_score

            # Countdown before the next message and screenshot
            countdown = 60  # Countdown in seconds
            while countdown > 0:
                if keyboard.is_pressed('q'):  # Check if the 'q' key is pressed to stop the script
                    app.update_message("Script stopped by user.")
                    break
                mins, secs = divmod(countdown, 60)
                timeformat = '{:02d}:{:02d}'.format(mins, secs)
                app.update_timer(f"Next message in {timeformat}")
                time.sleep(1)
                countdown -= 1
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console
            if keyboard.is_pressed('q'):  # Check if the 'q' key is pressed to stop the script
                break
    except KeyboardInterrupt:
        app.update_message("Script terminated.")

# Function to run the main script in a separate thread
def run_main():
    main_thread = Thread(target=main)
    main_thread.start()

if __name__ == "__main__":
    app = App()
    app.after(100, run_main)
    app.mainloop()
