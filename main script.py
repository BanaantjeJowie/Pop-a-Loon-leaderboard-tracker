import requests


ten_url = "https://pop-a-loon.stijnen.be/api/leaderboard?limit=10"
twenty_url = "https://pop-a-loon.stijnen.be/api/leaderboard?skip=10&limit=10"

headers = {
    'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU'
}



response = requests.get(twenty_url, headers=headers)
response.raise_for_status()
print(response.text)