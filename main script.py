import requests
import json
import os
from datetime import datetime

# Define the necessary URLs and headers
leaderboard_url = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10"
discord_webhook_url = "https://discord.com/api/webhooks/1247250306446790769/nx3UwUhZ_70OY5R-eT4Bal_y0vK1-PDXXAVrCRdlAMLK7FXzggj3cwwiZ3R_BmH0lcAJ"

headers = {
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU'
}

# File to store the previous leaderboard data and timestamp
data_file = 'previous_leaderboard.json'

# Fetch the leaderboard data
response = requests.get(leaderboard_url, headers=headers)
current_leaderboard = response.json()

# Load the previous leaderboard data from a local file
try:
    with open(data_file, 'r') as f:
        previous_data = json.load(f)
        previous_leaderboard = previous_data['topUsers']
        last_check_time = datetime.fromisoformat(previous_data['timestamp'])
except (FileNotFoundError, KeyError):
    previous_leaderboard = []
    last_check_time = datetime.now()

# Calculate the time since the last check
current_time = datetime.now()
time_diff = current_time - last_check_time
time_diff_str = str(time_diff).split('.')[0]  # Format the time difference

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
with open(data_file, 'w') as f:
    json.dump({
        'timestamp': current_time.isoformat(),
        'topUsers': current_leaderboard.get('topUsers', [])
    }, f)

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
            "avatar": "bb71f469c158984e265093a81b3397fb",
            "footer": {
                "text": f"Pops since the last check ({time_diff_str} ago).",
                "icon_url": "https://raw.githubusercontent.com/SimonStnn/pop-a-loon/main/resources/icons/icon-128.png"  
            }
        }
    ]
}

# Send the embed to Discord
requests.post(
    discord_webhook_url, 
    data=json.dumps(embed), 
    headers={"Content-Type": "application/json"}
)
