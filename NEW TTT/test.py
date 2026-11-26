import requests
import pandas as pd
import urllib3

urllib3.disable_warnings()

payload = {
    "reportName": "VisitorsLog Per Area",
    "@FromDate": "2026-11-20T06:00",
    "@ToDate": "2026-11-21T06:00",
    "@IncludePhotos": 0
}

username = "0180260"
password = "YOUR_PASSWORD"

response = requests.post(
    "http://10.39.215.77/report",
    auth=(username, password),
    data=payload,
    verify=False
)

print(response.status_code)
print(response.text[:1000])
