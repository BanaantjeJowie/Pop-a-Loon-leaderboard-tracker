import requests
import json

url = "https://pop-a-loon.stijnen.be/api/user/increment"

payload = {}
headers = {
  'authorization': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpZCI6IjY2MDZlYTI0OWZiZTg1ZDUyM2RkOWM1YiIsImlhdCI6MTcxMTcyOTE4OH0.qDSx4sGLHHArwWQT5husBehcXU2u0Hwsxh9Z9kS-ieU'
}

response = requests.request("GET", url, headers=headers, data=payload)
content = response.json()
