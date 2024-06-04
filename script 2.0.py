import requests
import json
import os
from datetime import datetime
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from flask import Flask, jsonify

# Define the necessary URLs and headers
leaderboard_url = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10"
#discord_webhook_url = "https://discord.com/api/webhooks/1247250306446790769/nx3UwUhZ_70OY5R-eT4Bal_y0vK1-PDXXAVrCRdlAMLK7FXzggj3cwwiZ3R_BmH0lcAJ?thread_id=1247513167278637138"
discord_webhook_url = "https://discord.com/api/webhooks/1247250306446790769/nx3UwUhZ_70OY5R-eT4Bal_y0vK1-PDXXAVrCRdlAMLK7FXzggj3cwwiZ3R_BmH0lcAJ"
headers = {
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU'
}

# File to store the previous leaderboard data and timestamp
data_file = 'previous_leaderboard.json'

def fetch_leaderboard():
    try:
        # Fetch the leaderboard data
        response = requests.get(leaderboard_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch leaderboard data: {e}")
        return None

def load_previous_data():
    try:
        with open(data_file, 'r') as f:
            previous_data = json.load(f)
            previous_leaderboard = previous_data['topUsers']
            last_check_time = datetime.fromisoformat(previous_data['timestamp'])
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        previous_leaderboard = []
        last_check_time = datetime.now()
    return previous_leaderboard, last_check_time

def save_current_data(current_leaderboard, current_time):
    try:
        with open(data_file, 'w') as f:
            json.dump({
                'timestamp': current_time.isoformat(),
                'topUsers': current_leaderboard.get('topUsers', [])
            }, f)
    except IOError as e:
        messagebox.showerror("Error", f"Failed to save leaderboard data: {e}")

def calculate_differences(current_leaderboard, previous_leaderboard):
    balloon_differences = {}
    for current_user in current_leaderboard.get('topUsers', []):
        for previous_user in previous_leaderboard:
            if current_user['username'] == previous_user['username']:
                balloon_differences[current_user['username']] = current_user['count'] - previous_user['count']
                break
        else:
            balloon_differences[current_user['username']] = current_user['count']
    return balloon_differences

def create_embed(current_leaderboard, balloon_differences, time_diff_str, filtered=False):
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

    if filtered:
        has_increases = False
        for user in current_leaderboard.get('topUsers', []):
            diff = balloon_differences.get(user['username'], user['count'])
            if diff > 0:
                has_increases = True
                username_field["value"] += f"{user['username']}\n"
                count_field["value"] += f"{user['count']}\n"
                pops_since_last_check_field["value"] += f"+{diff}\n"
        if not has_increases:
            username_field["value"] = "No increases"
            count_field["value"] = "-"
            pops_since_last_check_field["value"] = "-"
    else:
        for user in current_leaderboard.get('topUsers', []):
            diff = balloon_differences.get(user['username'], user['count'])
            username_field["value"] += f"{user['username']}\n"
            count_field["value"] += f"{user['count']}\n"
            pops_since_last_check_field["value"] += f"+{diff}\n"

    filtered_url = "http://localhost:5000/filtered_leaderboard"

    embed = {
        "embeds": [
            {
                "title": "Top 10 Poppers" if not filtered else " All increases",
                "thumbnail": {
                    "url": "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png"
                },
                "color": 16711680,
                "fields": [username_field, count_field, pops_since_last_check_field],
                "avatar": "bb71f469c158984e265093a81b3397fb",
                "footer": {
                    "text": f"Pops since the last check ({time_diff_str} ago).",
                    "icon_url": "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png"  
                },
                "components": [
                    {
                        "type": 1,
                        "components": [
                            {
                                "type": 2,
                                "label": "Show Increases Only",
                                "style": 5,
                                "url": filtered_url
                            }
                        ]
                    }
                ] if not filtered else []
            }
        ]
    }
    return embed

def send_to_discord(embed):
    response = requests.post(
        discord_webhook_url, 
        data=json.dumps(embed), 
        headers={"Content-Type": "application/json"}
    )

def check_leaderboard(filtered=False):
    current_leaderboard = fetch_leaderboard()
    if current_leaderboard is None:
        return

    previous_leaderboard, last_check_time = load_previous_data()
    current_time = datetime.now()
    time_diff = current_time - last_check_time
    time_diff_str = str(time_diff).split('.')[0]  # Format the time difference
    
    # Update the live timer label
    timer_label.config(text=f"Time since last check: {time_diff_str}")

    balloon_differences = calculate_differences(current_leaderboard, previous_leaderboard)
    save_current_data(current_leaderboard, current_time)

    embed = create_embed(current_leaderboard, balloon_differences, time_diff_str, filtered)
    send_to_discord(embed)

def create_filtered_leaderboard():
    try:
        # Load the previous leaderboard data
        with open(data_file, 'r') as f:
            previous_data = json.load(f)
            previous_leaderboard = previous_data['topUsers']
            last_check_time = datetime.fromisoformat(previous_data['timestamp'])
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        previous_leaderboard = []
        last_check_time = datetime.now()

    current_time = datetime.now()
    time_diff = current_time - last_check_time
    time_diff_str = str(time_diff).split('.')[0]

    current_leaderboard = fetch_leaderboard()
    balloon_differences = calculate_differences(current_leaderboard, previous_leaderboard)

    filtered_users = [user for user in current_leaderboard.get('topUsers', []) if balloon_differences.get(user['username'], user['count']) > 0]

    if not filtered_users:
        filtered_embed = {
            "embeds": [
                {
                    "title": "Top 10 Pop-A-Loon Suspects - Increases Only",
                    "color": 16711680,
                    "fields": [
                        {
                            "name": "Username",
                            "value": "No increases",
                            "inline": True
                        },
                        {
                            "name": "Count",
                            "value": "-",
                            "inline": True
                        },
                        {
                            "name": "Increase",
                            "value": "-",
                            "inline": True
                        }
                    ],
                    "avatar": "bb71f469c158984e265093a81b3397fb",
                    "footer": {
                        "text": f"Pops since the last check ({time_diff_str} ago).",
                        "icon_url": "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png"  
                    }
                }
            ]
        }
    else:
        filtered_username_field = {
            "name": "Username",
            "value": "",
            "inline": True
        }

        filtered_count_field = {
            "name": "Count",
            "value": "",
            "inline": True
        }

        filtered_pops_since_last_check_field = {
            "name": "Increase",
            "value": "",
            "inline": True
        }

        for user in filtered_users:
            diff = balloon_differences.get(user['username'], user['count'])
            filtered_username_field["value"] += f"{user['username']}\n"
            filtered_count_field["value"] += f"{user['count']}\n"
            filtered_pops_since_last_check_field["value"] += f"+{diff}\n"

        filtered_embed = {
            "embeds": [
                {
                    "title": "Top 10 Pop-A-Loon Suspects - Increases Only",
                    "color": 16711680,
                    "fields": [filtered_username_field, filtered_count_field, filtered_pops_since_last_check_field],
                    "avatar": "bb71f469c158984e265093a81b3397fb",
                    "footer": {
                        "text": f"Pops since the last check ({time_diff_str} ago).",
                        "icon_url": "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png"  
                    }
                }
            ]
        }

    return filtered_embed

# Flask app to serve the filtered leaderboard (if full interactivity is required)
app = Flask(__name__)

@app.route('/filtered_leaderboard')
def filtered_leaderboard():
    filtered_embed = create_filtered_leaderboard()
    return jsonify(filtered_embed)

if __name__ == "__main__":
    # Run the Flask app in a separate thread
    from threading import Thread
    flask_thread = Thread(target=lambda: app.run(debug=False, use_reloader=False))
    flask_thread.start()

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

    # Add the check buttons with some styling
    check_button_top10 = ttk.Button(frame, text="Check Top 10", command=lambda: check_leaderboard(filtered=False))
    check_button_top10.pack(pady=(5, 5))

    check_button_filtered = ttk.Button(frame, text="Increase only", command=lambda: check_leaderboard(filtered=True))
    check_button_filtered.pack(pady=(5, 5))

    # Run the Tkinter event loop
    root.mainloop()
