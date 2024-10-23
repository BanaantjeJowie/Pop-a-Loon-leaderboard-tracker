import requests
import json
import os
from datetime import datetime, timedelta

# Base URL
base_url = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10"

# Authorization header
headers = {
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU'
}

# Discord webhook URL
discord_webhook_url = 'https://discord.com/api/webhooks/1247250306446790769/nx3UwUhZ_70OY5R-eT4Bal_y0vK1-PDXXAVrCRdlAMLK7FXzggj3cwwiZ3R_BmH0lcAJ'

# File to persist scores and timestamp
score_file = "previous_scores.json"

# Load previous scores and timestamp from file
def load_previous_scores():
    if os.path.exists(score_file):
        with open(score_file, 'r') as file:
            try:
                data = file.read().strip()  # Check if the file contains any data
                if data:  # If file is not empty
                    return json.loads(data)
                else:
                    return {"scores": {}, "timestamp": None}  # Return default if empty
            except json.JSONDecodeError:
                return {"scores": {}, "timestamp": None}  # Return default if invalid JSON
    else:
        return {"scores": {}, "timestamp": None}  # Return default if file doesn't exist


# Save current scores and timestamp to file
def save_previous_scores(previous_scores, timestamp):
    with open(score_file, 'w') as file:
        json.dump({"scores": previous_scores, "timestamp": timestamp}, file)

# Function to fetch leaderboard data
def fetch_leaderboard(skip: int):
    url = f"{base_url}&skip={skip}"
    response = requests.get(url, headers=headers)
    response.raise_for_status()  # Raise exception if request failed
    return response.json()

# Function to calculate time since last check
def time_since_last_check(last_check):
    if last_check is None:
        return "First check"
    
    last_check_time = datetime.fromisoformat(last_check)
    elapsed_time = datetime.now() - last_check_time
    
    days, seconds = divmod(elapsed_time.total_seconds(), 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, _ = divmod(seconds, 60)
    
    return f"{int(days)} days, {int(hours)}:{int(minutes):02d}:{int(seconds):02d} ago"

# Function to send leaderboard to Discord
def send_to_discord(embed_content):
    data = {
        "embeds": [embed_content]
    }
    response = requests.post(discord_webhook_url, json=data)
    if response.status_code == 204:
        print("Message sent to Discord successfully!")
    else:
        print(f"Failed to send message to Discord: {response.status_code}, {response.text}")

# Function to create Discord embed
def create_discord_embed(all_users_sorted, previous_scores, last_check):
    leaderboard_text = ""
    for rank, user in enumerate(all_users_sorted, start=1):
        current_score = user['count']
        username = user['username']
        previous_score = previous_scores.get(username, current_score)  # Default to current if not found
        score_diff = current_score - previous_score
        change_text = f"{'+' if score_diff > 0 else ''}{score_diff}" if score_diff != 0 else ''
        leaderboard_text += f"{rank}. **{username}** - {current_score} {change_text}\n"
    
    # Time since last check
    time_diff = time_since_last_check(last_check)

    # Create embed content
    embed_content = {
    "title": "Top 10 Poppers",
    "color": 3066993,  # Green color
    "fields": [
        {
            "name": "Username",
            "value": "\n".join([user['username'] for user in all_users_sorted]),
            "inline": True
        },
        {
            "name": "Count",
            "value": "\n".join([str(user['count']) for user in all_users_sorted]),
            "inline": True
        },
        {
            "name": "Increase",
            "value": "\n".join([f"{'+' if (user['count'] - previous_scores.get(user['username'], 0)) > 0 else ''}{user['count'] - previous_scores.get(user['username'], 0)}" for user in all_users_sorted]),
            "inline": True
        }
    ],
    "footer": {
        "text": f"Pops since the last check ({time_diff}).",
        "icon_url": "https://cdn.discordapp.com/attachments/1247250118504091688/1298647067023118416/icon-128_1.png?ex=671a52d4&is=67190154&hm=7da3fb14f4949a6d42f2be120508a538d64198a04908f308d76c30373e82a761&"  # Placeholder for balloon icon
    },
    "thumbnail": {
        "url": "https://cdn.discordapp.com/attachments/1247250118504091688/1298647067023118416/icon-128_1.png?ex=671a52d4&is=67190154&hm=7da3fb14f4949a6d42f2be120508a538d64198a04908f308d76c30373e82a761&"  # Placeholder for a thumbnail image
    },
    "author": {
        "name": "Pop-a-loon Watchdog",  # Example author name
        "icon_url": "https://cdn.discordapp.com/attachments/1247513167278637138/1248939295679709276/file_6.png?ex=66657cdc&is=66642b5c&hm=64ab019e21c19b3b99fb61a462eeda1771822dafb91b5367ccacfe021a443387&"  # Placeholder for avatar image
    },
    "timestamp": datetime.now().isoformat()
}

    return embed_content

# Function to print and calculate differences in scores
def print_leaderboard_with_changes(all_users_sorted, previous_scores):
    for rank, user in enumerate(all_users_sorted, start=1):
        current_score = user['count']
        username = user['username']
        previous_score = previous_scores.get(username, current_score)  # Default to current if not found
        score_diff = current_score - previous_score
        print(f"{rank}. User: {username}, Score: {current_score} {'+' if score_diff > 0 else ''}{score_diff if score_diff != 0 else ''}")
        previous_scores[username] = current_score

# Main code to fetch, compare, display leaderboard changes and send to Discord
def main():
    # Load previous scores and timestamp from file
    data = load_previous_scores()
    previous_scores = data.get("scores", {})
    last_check = data.get("timestamp", None)

    # Fetch all users (up to 100)
    all_users = []
    for skip in range(0, 100, 10):
        data = fetch_leaderboard(skip)
        all_users.extend(data["topUsers"])

    # Sort all users by 'count' (score) in descending order
    all_users_sorted = sorted(all_users, key=lambda x: x['count'], reverse=True)

    # Print leaderboard with score changes
    print_leaderboard_with_changes(all_users_sorted, previous_scores)

    # Create and send the leaderboard as a Discord embed
    embed_content = create_discord_embed(all_users_sorted, previous_scores, last_check)
    send_to_discord(embed_content)

    # Save updated scores and the current timestamp to file
    current_timestamp = datetime.now().isoformat()
    save_previous_scores(previous_scores, current_timestamp)

if __name__ == "__main__":
    main()
