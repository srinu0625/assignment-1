# Create an Excel file from the uploaded chat history text
import pandas as pd
import re

input_path = "C:\\Users\\lenovo\\Downloads\\chat history.txt"
output_path = "C:\\Users\\lenovo\\Downloads\\chat_history.xlsx"

rows = []

with open(input_path, "r", encoding="utf-8", errors="ignore") as f:
    lines = f.readlines()

current_time = None
current_work = []

for line in lines:
    line = line.strip()
    # match timestamp like 6/13/2025 1:51 AM
    match = re.search(r"\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}\s+(AM|PM)", line)
    if match:
        if current_time and current_work:
            rows.append({
                "Timestamp": current_time,
                "Work Assigned / Update": " ".join(current_work)
            })
        current_time = match.group(0)
        current_work = []
    else:
        if line and not line.lower().startswith("image"):
            current_work.append(line)

# append last block
if current_time and current_work:
    rows.append({
        "Timestamp": current_time,
        "Work Assigned / Update": " ".join(current_work)
    })

df = pd.DataFrame(rows)
df.to_excel(output_path, index=False)

df.head(), output_path
