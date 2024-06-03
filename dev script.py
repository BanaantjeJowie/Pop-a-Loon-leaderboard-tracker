import requests
import json

url = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10"

payload = {}
headers = {
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MjI4OHQ5Ks-ieU'
}

try:
    response = requests.get(url, headers=headers, data=payload)
    response.raise_for_status()  # Check for HTTP errors
    
    # Parse the response as JSON
    data = response.json()
    
    # Save the data to a JSON file
    with open('leaderboard_data.json', 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
        
    print("Data saved to leaderboard_data.json")
except requests.exceptions.RequestException as e:
    print(f"An error occurred: {e}")
except json.JSONDecodeError:
    print("Failed to decode JSON response.")
