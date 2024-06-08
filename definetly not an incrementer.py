import requests
import json
import tkinter as tk
from tkinter import messagebox
import threading
import time

# Function to send the increment request
def increment_request():
    url = "https://pop-a-loon.stijnen.be/api/user/count/increment"
    headers = {
        'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps({}))
        response.raise_for_status()
        content = response.json()
        print(content)
        update_status("Incremented successfully", "green")
    except requests.exceptions.RequestException as e:
        print(e)
        update_status(f"Failed to increment: {e}", "red")

# Timer reset function
def reset_timer():
    global start_time
    start_time = time.time()

# Function to update the timer label
def update_timer():
    while True:
        elapsed_time = time.time() - start_time
        timer_label.config(text=f"Timer: {elapsed_time:.2f} seconds")
        time.sleep(0.1)

# Button click handler
def on_button_click():
    increment_request()
    reset_timer()

# Function to update the status label
def update_status(message, color):
    status_label.config(text=message, fg=color)

# Create the main application window
root = tk.Tk()
root.title("Increment GUI with Stopwatch")
root.geometry("300x400")

# Create and place the increment button
increment_button = tk.Button(root, text="Increment", command=on_button_click)
increment_button.pack(pady=20)

# Create and place the timer label
timer_label = tk.Label(root, text="Timer: 0.00 seconds")
timer_label.pack(pady=20)

# Create and place the status label
status_label = tk.Label(root, text="", fg="red")
status_label.pack(pady=20)

# Start the timer thread
start_time = time.time()
timer_thread = threading.Thread(target=update_timer, daemon=True)
timer_thread.start()

# Run the Tkinter main loop
root.mainloop()
