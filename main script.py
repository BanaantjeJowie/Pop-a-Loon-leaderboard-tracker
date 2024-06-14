import requests
import json
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from flask import Flask, jsonify
from threading import Thread
import schedule
import time

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
daily_data_file = 'daily_leaderboard.json'
hourly_check_times = [datetime.now().replace(minute=30, second=0, microsecond=0) + timedelta(hours=i) for i in range(24)]

def fetch_leaderboard():
    try:
        response = requests.get(leaderboard_url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        messagebox.showerror("Error", f"Failed to fetch leaderboard data: {e}")
        return None

def load_previous_data(file_name):
    try:
        with open(file_name, 'r') as f:
            previous_data = json.load(f)
            previous_leaderboard = previous_data['topUsers']
            last_check_time = datetime.fromisoformat(previous_data['timestamp'])
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        previous_leaderboard = []
        last_check_time = datetime.now()
    return previous_leaderboard, last_check_time

def save_current_data(file_name, current_leaderboard, current_time):
    try:
        with open(file_name, 'w') as f:
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

    previous_leaderboard, last_check_time = load_previous_data(data_file)
    current_time = datetime.now()
    time_diff = current_time - last_check_time
    time_diff_str = str(time_diff).split('.')[0]
    
    timer_label.config(text=f"Time since last check: {time_diff_str}")

    balloon_differences = calculate_differences(current_leaderboard, previous_leaderboard)
    save_current_data(data_file, current_leaderboard, current_time)

    embed = create_embed(current_leaderboard, balloon_differences, time_diff_str, filtered)

    selected_webhooks = [key for key, var in webhook_vars.items() if var.get() == 1]
    send_to_discord(embed, selected_webhooks)

    # Update the next check time
    next_check_time = min(t for t in hourly_check_times if t > current_time)
    update_countdown()

def check_daily_leaderboard():
    global next_check_time

    current_leaderboard = fetch_leaderboard()
    if current_leaderboard is None:
        return

    previous_leaderboard, last_check_time = load_previous_data(daily_data_file)
    current_time = datetime.now()
    time_diff = current_time - last_check_time
    time_diff_str = str(time_diff).split('.')[0]

    balloon_differences = calculate_differences(current_leaderboard, previous_leaderboard)
    save_current_data(daily_data_file, current_leaderboard, current_time)

    embed = create_embed(current_leaderboard, balloon_differences, time_diff_str)

    selected_webhooks = [key for key, var in webhook_vars.items() if var.get() == 1]
    send_to_discord(embed, selected_webhooks)

    # Update the next check time
    next_check_time = min(t for t in hourly_check_times if t > current_time)
    update_countdown()

def update_countdown():
    now = datetime.now()
    time_until_next_check = next_check_time - now
    hours, remainder = divmod(time_until_next_check.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    countdown_str = f"Time until next check: {hours:02}:{minutes:02}:{seconds:02}"
    countdown_label.config(text=countdown_str)
    countdown_label.after(1000, update_countdown)

def start_scheduled_checks():
    schedule.every().hour.at(":30").do(check_leaderboard)
    schedule.every().day.at("00:01").do(check_daily_leaderboard)

    while True:
        schedule.run_pending()
        time.sleep(1)

def run_flask():
    app = Flask(__name__)

    @app.route('/filtered_leaderboard')
    def filtered_leaderboard():
        check_leaderboard(filtered=True)
        return jsonify({"message": "Filtered leaderboard sent to Discord"})

    app.run(port=5000)

def start_gui():
    global timer_label, countdown_label, webhook_vars

    root = tk.Tk()
    root.title("Pop-a-loon Leaderboard Tracker")

    mainframe = ttk.Frame(root, padding="10 10 10 10")
    mainframe.grid(column=0, row=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    timer_label = ttk.Label(mainframe, text="Time since last check: N/A")
    timer_label.grid(column=0, row=0, columnspan=2)

    countdown_label = ttk.Label(mainframe, text="Time until next check: N/A")
    countdown_label.grid(column=0, row=1, columnspan=2)

    webhook_vars = {key: tk.IntVar(value=1) for key in webhook_urls.keys()}

    for i, (key, var) in enumerate(webhook_vars.items(), start=2):
        ttk.Checkbutton(mainframe, text=key, variable=var).grid(column=0, row=i, sticky=tk.W)

    ttk.Button(mainframe, text="Manual Check", command=lambda: check_leaderboard(filtered=False)).grid(column=0, row=i+1)
    ttk.Button(mainframe, text="Manual Check (Filtered)", command=lambda: check_leaderboard(filtered=True)).grid(column=1, row=i+1)

    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    next_check_time = min(t for t in hourly_check_times if t > datetime.now())
    update_countdown()

    root.mainloop()

if __name__ == "__main__":
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    scheduler_thread = Thread(target=start_scheduled_checks, daemon=True)
    scheduler_thread.start()

    start_gui()
