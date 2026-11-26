import subprocess

result = subprocess.run(
    ["curl.exe", "--version"],
    capture_output=True,
    text=True
)

print(result.stdout)
print(result.stderr)