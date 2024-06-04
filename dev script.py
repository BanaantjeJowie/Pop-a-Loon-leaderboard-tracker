import requests
import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk

# Define the necessary URLs and headers
leaderboard_url = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10"
discord_webhook_url = "https://discord.com/api/webhooks/1247250306446790769/nx3UwUhZ_70OY5R-eT4Bal_y0vK1-PDXXAVrCRdlAMLK7FXzggj3cwwiZ3R_BmH0lcAJ"

headers = {
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU'
}

# File to store the previous leaderboard data and timestamp
data_file = 'previous_leaderboard.json'

def check_leaderboard():
    try:
        # Fetch the leaderboard data
        response = requests.get(leaderboard_url, headers=headers)
        response.raise_for_status()
        current_leaderboard = response.json()
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch leaderboard data: {e}")
        return

    # Load the previous leaderboard data from a local file
    try:
        with open(data_file, 'r') as f:
            previous_data = json.load(f)
            previous_leaderboard = previous_data['topUsers']
            last_check_time = datetime.fromisoformat(previous_data['timestamp'])
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        previous_leaderboard = []
        last_check_time = datetime.now()

    # Calculate the time since the last check
    current_time = datetime.now()
    time_diff = current_time - last_check_time
    time_diff_str = str(time_diff).split('.')[0]  # Format the time difference
    
    # Update the live timer label
    timer_label.config(text=f"Time since last check: {time_diff_str}")

    # Calculate the number of popped balloons since the last check
    balloon_differences = {}
    for current_user in current_leaderboard.get('topUsers', []):
        for previous_user in previous_leaderboard:
            if current_user['username'] == previous_user['username']:
                balloon_differences[current_user['username']] = current_user['count'] - previous_user['count']
                break
        else:
            balloon_differences[current_user['username']] = current_user['count']

    # Save the current leaderboard data with the current timestamp for future comparison
    try:
        with open(data_file, 'w') as f:
            json.dump({
                'timestamp': current_time.isoformat(),
                'topUsers': current_leaderboard.get('topUsers', [])
            }, f)
    except IOError as e:
        messagebox.showerror("Error", f"Failed to save leaderboard data: {e}")
        return

    # Create the Discord embed message
    username_field = {
        "name": "Username",
        "value": "",
        "inline": True
    }

    count_field = {
        "name": "Count",
        "value": "",
        "inline": True
    }

    pops_since_last_check_field = {
        "name": "Increase",
        "value": "",
        "inline": True
    }

    for user in current_leaderboard.get('topUsers', []):
        diff = balloon_differences.get(user['username'], user['count'])
        username_field["value"] += f"{user['username']}\n"
        count_field["value"] += f"{user['count']}\n"
        pops_since_last_check_field["value"] += f"+{diff}\n"

    embed = {
        "embeds": [
        {
            "title": "Top 10 Pop-A-Loon Suspects.",
            "color": 16711680,
            "fields": [username_field, count_field, pops_since_last_check_field],
            "footer": {
                "text": f"Pops since the last check ({time_diff_str} ago).",
                "icon_url": "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png"  
            }
        }
    ]
    }

    # Send the embed to Discord
    response = requests.post(
            discord_webhook_url, 
            data=json.dumps(embed), 
            headers={"Content-Type": "application/json"}
        )



# Set up the Tkinter window
root = tk.Tk()
root.title("Pop-A-Loon Leaderboard Checker")

# Set the window size
height = 200
width = 400
root.geometry(f"{width}x{height}")

# Add padding and background color
root.configure(bg="#f0f0f0")
root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=1)

# Add a frame for better organization
frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
frame.grid(sticky="nsew")

# Add a title label
title_label = tk.Label(frame, text="Check on leaderboard.", font=("Helvetica", 16), bg="#f0f0f0")
title_label.pack(pady=(0, 10))

# Add the live timer label
timer_label = tk.Label(frame, text="", font=("Helvetica", 10), bg="#f0f0f0")
timer_label.pack(pady=(0, 10))

# Add the check button with some styling
check_button = ttk.Button(frame, text="Check", command=check_leaderboard)
check_button.pack(pady=10)

# Run the Tkinter event loop
root.mainloop()

