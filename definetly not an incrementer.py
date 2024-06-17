import requests
import json
import tkinter as tk
from tkinter import messagebox
import threading
import time
import random
# edge auth token
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2NjVhMzYxNTQzYmUyOTc0ZGViNDFmMiIsImlhdCI6MTcxNzkzNjk5M30.tcd4jL3eTblFBaH0kyS9MZKdT6Y2aK3H-I5Doql2Qak

#main auth token
#eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU


# Function to send the increment request
def increment_request():
    url = "https://pop-a-loon.stijnen.be/api/user/count/increment"
    headers = {
        'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2NjVhMzYxNTQzYmUyOTc0ZGViNDFmMiIsImlhdCI6MTcxNzkzNjk5M30.tcd4jL3eTblFBaH0kyS9MZKdT6Y2aK3H-I5Doql2Qak8',
        'Content-Type': 'application/json'
    }
    try:
        response = requests.post(url, headers=headers, data=json.dumps({}))
        response.raise_for_status()
        content = response.json()
        # Update count in GUI
        count_label.config(text=f"Count: {content['count']}")
        update_status("Incremented successfully", "green")
    except requests.exceptions.RequestException as e:
        print(e)
        update_status(f"Failed to increment", "red")

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

# Function to update the countdown label
def update_countdown():
    while auto_increment_running:
        remaining_time = next_increment_time - time.time()
        if remaining_time <= 0:
            increment_request()
            schedule_next_increment()
        else:
            countdown_label.config(text=f"Next increment in: {remaining_time:.2f} seconds")
        time.sleep(0.1)

# Schedule the next automatic increment
def schedule_next_increment():
    global next_increment_time
    next_increment_time = time.time() + random.randint(120, 300)
    countdown_label.config(text=f"Next increment in: {next_increment_time - time.time():.2f} seconds")

# Start automatic incrementing
def start_auto_increment():
    global auto_increment_running
    auto_increment_running = True
    schedule_next_increment()
    countdown_thread = threading.Thread(target=update_countdown, daemon=True)
    countdown_thread.start()
    update_status("Auto increment started", "green")

# Stop automatic incrementing
def stop_auto_increment():
    global auto_increment_running
    auto_increment_running = False
    countdown_label.config(text="Auto increment stopped")
    update_status("Auto increment stopped", "red")

# Button click handler
def on_button_click():
    increment_request()
    reset_timer()

# Function to update the status label
def update_status(message, color):
    status_label.config(text=message, fg=color)

# Create the main application window
root = tk.Tk()
root.title("Increment Pop-a-Loon count")
root.geometry("500x500")

# Create and place the title label
title_label = tk.Label(root, text="Pop-a-Loon incrementer", font=("Helvetica", 16))
title_label.pack(pady=10)

# Create and place the increment button
increment_button = tk.Button(root, text="Increment", command=on_button_click)
increment_button.pack(pady=10)

# Create and place the timer label
timer_label = tk.Label(root, text="Timer: 0.00 seconds")
timer_label.pack(pady=10)

# Create and place the status label
status_label = tk.Label(root, text="", fg="red")
status_label.pack(pady=10)

# Create and place the auto increment button
auto_increment_button = tk.Button(root, text="Start", command=start_auto_increment)
auto_increment_button.pack(pady=10)

# Create and place the stop button
stop_button = tk.Button(root, text="Stop ", command=stop_auto_increment)
stop_button.pack(pady=10)

# Create and place the countdown label
countdown_label = tk.Label(root, text="Next increment in: 0.00 seconds")
countdown_label.pack(pady=10)

# Create and place the count label
count_label = tk.Label(root, text="Count: 0")
count_label.pack(pady=10)

# Start the timer thread
start_time = time.time()
timer_thread = threading.Thread(target=update_timer, daemon=True)
timer_thread.start()

# Initialize auto increment variables
auto_increment_running = False
next_increment_time = 0

# Run the Tkinter main loop
root.mainloop()
