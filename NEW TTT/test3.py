import subprocess
import pandas as pd

username = input("Username: ")
password = input("Password: ")

cmd = [
    "curl.exe",
    "-k",
    "-u",
    f"{username}:{password}",
    "https://10.39.215.77/report"
]

result = subprocess.run(
    cmd,
    capture_output=True,
    text=Tr*e
)

print(result.stdout[:1000])

tables = pd.read_html(result.stdout)

print(tables[0].head())