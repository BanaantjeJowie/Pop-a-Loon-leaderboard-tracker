import pyautogui
import time
import keyboard
import pytesseract
from PIL import Image
import os
from typing import Dict, Tuple
import re
from datetime import datetime, timedelta
import json

# Configure Tesseract path (change this path to where Tesseract is installed on your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

SCORES_FILE = 'scores.json'

def type_text(text: str, interval: float = 0.05) -> None:
    for char in text:
        pyautogui.typewrite(char)
        time.sleep(interval)
    pyautogui.press('enter')
    time.sleep(0.05)
    pyautogui.press('enter')

def capture_and_read_text(region: Tuple[int, int, int, int]) -> str:
    print("Capturing screenshot in 5 seconds...")
    for i in range(5, 0, -1):
        print(f"{i}...", end='\r')
        time.sleep(1)
    print("Capturing screenshot now!")
    screenshot = pyautogui.screenshot(region=region)
    screenshot.save('captured_text.png')
    try:
        text = pytesseract.image_to_string(Image.open('captured_text.png'))
    except Exception as e:
        print(f"Error during OCR: {e}")
        text = ""
    return text

def process_text(text: str) -> Dict[str, int]:
    lines = text.split('\n')
    scores = {}
    pattern = re.compile(r'^(.*\S)\s+(\d+)$')

    for line in lines:
        match = pattern.match(line)
        if match:
            username, score = match.groups()
            scores[username] = int(score)
    
    return scores

def save_scores(scores: Dict[str, int], filename: str = SCORES_FILE) -> None:
    data = {
        "timestamp": datetime.now().isoformat(),
        "scores": scores
    }
    with open(filename, 'w') as file:
        json.dump(data, file)

def load_scores(filename: str = SCORES_FILE) -> Tuple[Dict[str, int], datetime]:
    if not os.path.exists(filename):
        return {}, None
    
    try:
        with open(filename, 'r') as file:
            data = json.load(file)
            timestamp = datetime.fromisoformat(data['timestamp'])
            scores = data['scores']
            return scores, timestamp
    except (json.JSONDecodeError, KeyError) as e:
        print(f"Error loading scores: {e}")
        return {}, None

def initialize_script(countdown: int = 5) -> None:
    print("Starting script in 5 seconds...")
    for i in range(countdown, 0, -1):
        print(f"{i}...", end='\r')
        time.sleep(1)
    print("Script starting now!")

def main_loop(region: Tuple[int, int, int, int], text_to_type: str) -> None:
    initialize_script()
    previous_scores, last_run_time = load_scores()

    if last_run_time:
        current_time = datetime.now()
        time_diff = current_time - last_run_time

        days = time_diff.days
        hours, remainder = divmod(time_diff.seconds, 3600)
        minutes, _ = divmod(remainder, 60)

        time_since_last_run = ""
        if days > 0:
            time_since_last_run += f"{days} days, "
        if hours > 0:
            time_since_last_run += f"{hours} hours, "
        if minutes > 0:
            time_since_last_run += f"{minutes} minutes"
        time_since_last_run = time_since_last_run.rstrip(", ")

        print(f"Time since last run: {time_since_last_run}")

    try:
        while True:
            if keyboard.is_pressed('q'):
                print("Script stopped by user.")
                break

            type_text(text_to_type)

            captured_text = capture_and_read_text(region)
            current_scores = process_text(captured_text)

            for username, current_score in current_scores.items():
                previous_score = previous_scores.get(username, None)
                if previous_score is None:
                    previous_scores[username] = current_score
                    continue
                increment = current_score - previous_score
                if increment > 0:
                    time_since_last_check = f"({time_since_last_run} since last check)"
                    result_text = f"{username} popped {increment} Balloons {time_since_last_check}."
                    type_text(result_text)
                previous_scores[username] = current_score

            save_scores(previous_scores)

            countdown_timer(60)

            if keyboard.is_pressed('q'):
                break
    except KeyboardInterrupt:
        print("Script terminated.")

def countdown_timer(seconds: int) -> None:
    RED = "\033[91m"
    RESET = "\033[0m"
    countdown = seconds
    while countdown > 0:
        if keyboard.is_pressed('q'):
            print("Script stopped by user.")
            break
        mins, secs = divmod(countdown, 60)
        timeformat = '{:02d}:{:02d}'.format(mins, secs)
        print(f"{RED}Next message in {timeformat}{RESET}", end='\r')
        time.sleep(1)
        countdown -= 1
    os.system('cls' if os.name == 'nt' else 'clear')

def main() -> None:
    text_to_type = "/pop-a-loon"
    region = (1468, 611, 188, 251)

    main_loop(region, text_to_type)

if __name__ == "__main__":
    main()
