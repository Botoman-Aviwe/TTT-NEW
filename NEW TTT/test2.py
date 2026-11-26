import requests
import urllib3

urllib3.disable_warnings()

r = requests.get(
    "http://10.39.215.77",
    auth=("0180260", "YOUR_PASSWORD"),
    verify=False
)

print(r.status_code)
print(r.headers)
    