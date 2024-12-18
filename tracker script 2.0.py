import requests
import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from flask import Flask, jsonify
from threading import Thread

leaderboard_url = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10"
webhook_urls = {
    "main": "https://discord.com/api/webhooks/1247250306446790769/nx3UwUhZ_70OY5R-eT4Bal_y0vK1-PDXXAVrCRdlAMLK7FXzggj3cwwiZ3R_BmH0lcAJ",
    "simon": "https://discord.com/api/webhooks/1247919630958461038/6MK3C7S9ggIpOM-tmbXd2iCkSrM7Trai27ROLBVhaWrQKU_RdsbY8nNoz6rlFpeEsMtj",
    "test": "https://discord.com/api/webhooks/1247250306446790769/nx3UwUhZ_70OY5R-eT4Bal_y0vK1-PDXXAVrCRdlAMLK7FXzggj3cwwiZ3R_BmH0lcAJ?thread_id=1247513167278637138",
    "new_webhook": "https://discord.com/api/webhooks/1249447140229644439/96A0UnCKqbBrXpYhmDikQuKdKsc5Hh33Apsxqyh-MAWSrYtoVOG6IMoo2gc_RvzpFw4c"
}
headers = {
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU'
}

data_file = 'previous_leaderboard.json'
check_interval = 3600

def fetch_leaderboard():
    try:
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
        current_user_id = current_user['id']
        current_user_count = current_user['count']
        for previous_user in previous_leaderboard:
            if current_user_id == previous_user['id']:
                balloon_differences[current_user_id] = {
                    'username': current_user['username'],
                    'count_diff': current_user_count - previous_user['count']
                }
                break
        else:
            balloon_differences[current_user_id] = {
                'username': current_user['username'],
                'count_diff': current_user_count
            }
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
            user_id = user['id']
            diff_info = balloon_differences.get(user_id, {'username': user['username'], 'count_diff': user['count']})
            if diff_info['count_diff'] > 0:
                has_increases = True
                username_field["value"] += f"{diff_info['username']}\n"
                count_field["value"] += f"{user['count']}\n"
                pops_since_last_check_field["value"] += f"+{diff_info['count_diff']}\n"
        if not has_increases:
            username_field["value"] = "No increases"
            count_field["value"] = "-"
            pops_since_last_check_field["value"] = "-"
    else:
        for user in current_leaderboard.get('topUsers', []):
            user_id = user['id']
            diff_info = balloon_differences.get(user_id, {'username': user['username'], 'count_diff': user['count']})
            username_field["value"] += f"{diff_info['username']}\n"
            count_field["value"] += f"{user['count']}\n"
            pops_since_last_check_field["value"] += f"+{diff_info['count_diff']}\n"

    filtered_url = "http://localhost:5000/filtered_leaderboard"

    embed = { "avatar_url": "https://cdn.discordapp.com/attachments/1247513167278637138/1248939295679709276/file_6.png?ex=66657cdc&is=66642b5c&hm=64ab019e21c19b3b99fb61a462eeda1771822dafb91b5367ccacfe021a443387&",
        "embeds": [
            {
                "title": "Top 10 Poppers" if not filtered else "All increases",
                "thumbnail": {
                    "url": "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png"
                },
                "color": 16711680,
                "fields": [username_field, count_field, pops_since_last_check_field],
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

def send_to_discord(embed, selected_webhooks):
    for name in selected_webhooks:
        url = webhook_urls.get(name)
        if url:
            requests.post(
                url, 
                data=json.dumps(embed), 
                headers={"Content-Type": "application/json"}
            )

def check_leaderboard(filtered=False):
    global next_check_time

    current_leaderboard = fetch_leaderboard()
    if current_leaderboard is None:
        return

    previous_leaderboard, last_check_time = load_previous_data()
    current_time = datetime.now()
    time_diff = current_time - last_check_time
    time_diff_str = str(time_diff).split('.')[0]
    
    timer_label.config(text=f"Time since last check: {time_diff_str}")

    balloon_differences = calculate_differences(current_leaderboard, previous_leaderboard)
    save_current_data(current_leaderboard, current_time)

    embed = create_embed(current_leaderboard, balloon_differences, time_diff_str, filtered)

    selected_webhooks = [key for key, var in webhook_vars.items() if var.get() == 1]
    send_to_discord(embed, selected_webhooks)

    next_check_time = current_time + timedelta(seconds=check_interval)
    update_countdown()

def schedule_next_check():
    root.after(check_interval * 1000, check_leaderboard)

def update_countdown():
    global next_check_time

    if next_check_time:
        time_left = next_check_time - datetime.now()
        if time_left.total_seconds() > 0:
            countdown_label.config(text=f"Time until next check: {str(time_left).split('.')[0]}")
            root.after(1000, update_countdown)
        else:
            countdown_label.config(text="Time until next check: 00:00:00")
            check_leaderboard()

def create_filtered_leaderboard():
    try:
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

    filtered_users = [user for user in current_leaderboard.get('topUsers', []) if balloon_differences.get(user['id'], {'count_diff': user['count']})['count_diff'] > 0]

    if not filtered_users:
        filtered_embed = {"avatar_url": "https://cdn.discordapp.com/attachments/1247513167278637138/1248939295679709276/file_6.png?ex=66657cdc&is=66642b5c&hm=64ab019e21c19b3b99fb61a462eeda1771822dafb91b5367ccacfe021a443387&",
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
            user_id = user['id']
            diff_info = balloon_differences.get(user_id, {'username': user['username'], 'count_diff': user['count']})
            filtered_username_field["value"] += f"{diff_info['username']}\n"
            filtered_count_field["value"] += f"{user['count']}\n"
            filtered_pops_since_last_check_field["value"] += f"+{diff_info['count_diff']}\n"

        filtered_embed = {"avatar_url": "https://cdn.discordapp.com/attachments/1247513167278637138/1248939295679709276/file_6.png?ex=66657cdc&is=66642b5c&hm=64ab019e21c19b3b99fb61a462eeda1771822dafb91b5367ccacfe021a443387&",
            "embeds": [
                {
                    "title": "Top 10 Pop-A-Loon Suspects - Increases Only",
                    "color": 16711680,
                    "fields": [filtered_username_field, filtered_count_field, filtered_pops_since_last_check_field],
                    "footer": {
                        "text": f"Pops since the last check ({time_diff_str} ago).",
                        "icon_url": "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png"  
                    }
                }
            ]
        }

    return filtered_embed

app = Flask(__name__)

@app.route('/filtered_leaderboard')
def filtered_leaderboard():
    filtered_embed = create_filtered_leaderboard()
    return jsonify(filtered_embed)

def start_automatic_checks():
    global next_check_time
    next_check_time = datetime.now() + timedelta(seconds=check_interval)
    update_countdown()
    schedule_next_check()

if __name__ == "__main__":
    flask_thread = Thread(target=lambda: app.run(debug=False, use_reloader=False))
    flask_thread.start()

    root = tk.Tk()
    root.title("Pop-A-Loon Leaderboard Checker")

    
    root.geometry(f"400x500")

    root.configure(bg="#f0f0f0")
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)

    frame = tk.Frame(root, bg="#f0f0f0", padx=20, pady=20)
    frame.grid(sticky="nsew")

    title_label = tk.Label(frame, text="Check on leaderboard.", font=("Helvetica", 16), bg="#f0f0f0")
    title_label.pack(pady=(0, 10))

    timer_label = tk.Label(frame, text="", font=("Helvetica", 10), bg="#f0f0f0")
    timer_label.pack(pady=(0, 10))

    countdown_label = tk.Label(frame, text="", font=("Helvetica", 10), bg="#f0f0f0")
    countdown_label.pack(pady=(0, 10))

    webhook_vars = {
        "main": tk.IntVar(),
        "simon": tk.IntVar(),
        "test": tk.IntVar(),
        "new_webhook": tk.IntVar()
    }

    checkbox_main = tk.Checkbutton(frame, text="E-ICT", variable=webhook_vars["main"], bg="#f0f0f0")
    checkbox_main.pack(anchor="w")

    checkbox_simon = tk.Checkbutton(frame, text="Simon", variable=webhook_vars["simon"], bg="#f0f0f0")
    checkbox_simon.pack(anchor="w")

    checkbox_test = tk.Checkbutton(frame, text="Test channel", variable=webhook_vars["test"], bg="#f0f0f0")
    checkbox_test.pack(anchor="w")

    checkbox_new = tk.Checkbutton(frame, text="Bananenland", variable=webhook_vars["new_webhook"], bg="#f0f0f0")
    checkbox_new.pack(anchor="w")

    check_button_top10 = ttk.Button(frame, text="Check Top 10", command=lambda: check_leaderboard(filtered=False))
    check_button_top10.pack(pady=(5, 5))

    check_button_filtered = ttk.Button(frame, text="Increase only", command=lambda: check_leaderboard(filtered=True))
    check_button_filtered.pack(pady=(5, 5))

    start_button = ttk.Button(frame, text="Start Automatic Checks", command=start_automatic_checks)
    start_button.pack(pady=(10, 10))

    root.mainloop()
