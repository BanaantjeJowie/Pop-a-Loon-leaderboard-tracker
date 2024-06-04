import requests
import json
import time
import random

url = "https://pop-a-loon.stijnen.be/api/user/count/increment"

payload = {}
headers = {
  'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU',
  'Content-Type': 'application/json'
}

try:
    while True:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        content = response.json()
        print(content)
        
        # Wait for a random interval between 5 and 15 minutes
        interval = random.randint(1, 10) * 60
        print(f"Waiting for {interval} seconds...")
        time.sleep(interval)
        
except KeyboardInterrupt:
    print("Script stopped by user.")
