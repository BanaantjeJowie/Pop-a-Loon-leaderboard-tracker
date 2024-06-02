import pyautogui
import time
import keyboard
import pytesseract
from PIL import Image
import os

# Configure Tesseract path (change this path to where Tesseract is installed on your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def type_text(text, interval=0.05):
    for char in text:
        pyautogui.typewrite(char)
        time.sleep(interval)
    pyautogui.press('enter')
    time.sleep(0.5)
    pyautogui.press('enter')

def capture_and_read_text(region):
    print("Capturing screenshot in 5 seconds...")
    for i in range(5, 0, -1):
        print(f"{i}...", end='\r')
        time.sleep(1)
    print("Capturing screenshot now!")
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save('captured_text.png')
    text = pytesseract.image_to_string(Image.open('captured_text.png'))
    return text

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

def main():
    text_to_type = "/pop-a-loon"
    RED = "\033[91m"
    RESET = "\033[0m"
    region = (1303, 564, 194, 272)  # Replace with the actual region coordinates of the screenshot.

    previous_scores = {}

    print("Starting script in 5 seconds...")
    for i in range(5, 0, -1):
        print(f"{i}...", end='\r')
        time.sleep(1)
    print("Script starting now!")

    try:
        while True:
            if keyboard.is_pressed('q'):  # Check if the 'q' key is pressed
                print("Script stopped by user.")
                break

            type_text(text_to_type)

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

            countdown = 60  # Countdown in seconds before the next message and screenshot
            while countdown > 0:
                if keyboard.is_pressed('q'):  # Check if the 'q' key is pressed during countdown
                    print("Script stopped by user.")
                    break
                mins, secs = divmod(countdown, 60)
                timeformat = '{:02d}:{:02d}'.format(mins, secs)
                print(f"{RED}Next message in {timeformat}{RESET}", end='\r')
                time.sleep(1)
                countdown -= 1
            os.system('cls' if os.name == 'nt' else 'clear')  # Clear the console
            if keyboard.is_pressed('q'):  # Break the outer loop if 'q' is pressed
                break
    except KeyboardInterrupt:
        print("Script terminated.")

if __name__ == "__main__":
    main()
