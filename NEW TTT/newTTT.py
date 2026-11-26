import os
import requests
import urllib3
import pandas as pd
import tkinter as tk

from tkinter import ttk
from tkinter import messagebox

urllib3.disable_warnings()

# =========================================
# CONFIGURATION
# =========================================

REPORT_URL = "http://10.39.215.77/report"

# =========================================
# RETRIEVE REPORT
# =========================================

def retrieve_and_process():

    try:

        status.set("Retrieving data...")
        progress.start()

        payload = {
            "reportName": "VisitorsLog Per Area",
            "@FromDate": start_date_var.get(),
            "@ToDate": end_date_var.get(),
            "@IncludePhotos": 0
        }

        response = requests.post(
            REPORT_URL,
            data=payload,
            verify=False,
            timeout=120
        )

        tables = pd.read_html(response.text)

        if len(tables) == 0:

            raise Exception(
                "No table was returned from Versatech."
            )

        df = tables[0]

        process_ttt(df)

    except Exception as e:

        messagebox.showerror(
            "Error",
            str(e)
        )

        status.set("Error")

    finally:

        progress.stop()


# =========================================
# PROCESS TTT
# =========================================

def process_ttt(df):

    required_columns = [
        "IdNumber",
        "TimeDate",
        "Direction"
    ]

    for col in required_columns:

        if col not in df.columns:

            raise Exception(
                f"Column missing: {col}"
            )

    df["TimeDate"] = pd.to_datetime(df["TimeDate"])

    df = df.sort_values(
        ["IdNumber", "TimeDate"]
    )

    results = []

    for id_num, group in df.groupby("IdNumber"):

        arrive_time = None

        for _, row in group.iterrows():

            if row["Direction"] == "Arrive":

                arrive_time = row["TimeDate"]

            elif (
                row["Direction"] == "Depart"
                and arrive_time is not None
            ):

                minutes = (
                    row["TimeDate"] -
                    arrive_time
                ).total_seconds() / 60

                results.append({

                    "IdNumber": id_num,

                    "ArriveTime":
                    arrive_time,

                    "DepartTime":
                    row["TimeDate"],

                    "MinutesInTerminal":
                    round(minutes, 2)

                })

                arrive_time = None

    result_df = pd.DataFrame(results)

    if result_df.empty:

        messagebox.showwarning(
            "No Data",
            "No Arrive/Depart pairs found."
        )

        return

    total_minutes = result_df[
        "MinutesInTerminal"
    ].sum()

    total_trips = result_df[
        "MinutesInTerminal"
    ].count()

    average_ttt = (
        total_minutes /
        total_trips
    )

    fact_terminal = result_df.copy()

    fact_terminal["Date"] = (
        fact_terminal["ArriveTime"]
        .dt.date
    )

    fact_terminal["Hour"] = (
        fact_terminal["ArriveTime"]
        .dt.hour
    )

    fact_terminal["Shift"] = (
        fact_terminal["Hour"]
        .apply(
            lambda h:
            "Day Shift"
            if 6 <= h < 18
            else "Night Shift"
        )
    )

    summary_terminal = (

        fact_terminal

        .groupby("IdNumber")

        .agg(

            TotalMinutes=(
                "MinutesInTerminal",
                "sum"
            ),

            TripCount=(
                "MinutesInTerminal",
                "count"
            ),

            AvgMinutes=(
                "MinutesInTerminal",
                "mean"
            )

        )

        .reset_index()

    )

    summary_terminal["TTT"] = (

        summary_terminal[
            "TotalMinutes"
        ]

        /

        summary_terminal[
            "TripCount"
        ]

    )

    output_folder = "Output"

    os.makedirs(
        output_folder,
        exist_ok=True
    )

    result_df.to_excel(

        os.path.join(
            output_folder,
            "Terminal_Turnaround.xlsx"
        ),

        index=False

    )

    fact_terminal.to_excel(

        os.path.join(
            output_folder,
            "Fact_TerminalTurnaround.xlsx"
        ),

        index=False

    )

    summary_terminal.to_excel(

        os.path.join(
            output_folder,
            "Summary_TerminalTurnaround.xlsx"
        ),

        index=False

    )

    minutes_var.set(
        f"{total_minutes:,.2f}"
    )

    trips_var.set(
        str(total_trips)
    )

    ttt_var.set(
        f"{average_ttt:.2f} Minutes"
    )

    status.set(
        "Completed Successfully"
    )

    messagebox.showinfo(

        "Success",

        f"Reports saved to:\n{output_folder}"

    )


# =========================================
# GUI
# =========================================

root = tk.Tk()

root.title(
    "Terminal Turnaround Time System"
)

root.state("zoomed")

root.configure(
    bg="white"
)

# =========================================
# HEADER
# =========================================

header = tk.Frame(
    root,
    bg="#003366",
    height=80
)

header.pack(
    fill="x"
)

title = tk.Label(
    header,
    text="Terminal Turnaround Time System",
    bg="#003366",
    fg="white",
    font=(
        "Segoe UI",
        24,
        "bold"
    )
)

title.pack(
    pady=20
)

# =========================================
# MAIN FRAME
# =========================================

main_frame = tk.Frame(
    root,
    bg="#F2F4F7"
)

main_frame.pack(
    fill="both",
    expand=True,
    padx=20,
    pady=20
)

# START DATE

tk.Label(
    main_frame,
    text="Start Date",
    font=("Segoe UI", 12)
).pack()

start_date_var = tk.StringVar(
    value="2026-11-20T06:00"
)

tk.Entry(
    main_frame,
    textvariable=start_date_var,
    width=30,
    font=("Segoe UI", 11)
).pack(
    pady=5
)

# END DATE

tk.Label(
    main_frame,
    text="End Date",
    font=("Segoe UI", 12)
).pack()

end_date_var = tk.StringVar(
    value="2026-11-21T06:00"
)

tk.Entry(
    main_frame,
    textvariable=end_date_var,
    width=30,
    font=("Segoe UI", 11)
).pack(
    pady=5
)

# BUTTON

retrieve_btn = tk.Button(

    main_frame,

    text="Retrieve & Process",

    width=25,

    height=2,

    bg="#009933",

    fg="white",

    font=(
        "Segoe UI",
        12,
        "bold"
    ),

    command=retrieve_and_process

)

retrieve_btn.pack(
    pady=15
)

# PROGRESS BAR

progress = ttk.Progressbar(

    main_frame,

    orient="horizontal",

    mode="indeterminate",

    length=500

)

progress.pack(
    pady=15
)

# KPI VARIABLES

minutes_var = tk.StringVar(
    value="0"
)

trips_var = tk.StringVar(
    value="0"
)

ttt_var = tk.StringVar(
    value="0"
)

tk.Label(
    main_frame,
    text="Total Minutes",
    font=("Segoe UI", 12, "bold")
).pack()

tk.Label(
    main_frame,
    textvariable=minutes_var,
    font=("Segoe UI", 22)
).pack()

tk.Label(
    main_frame,
    text="Trips",
    font=("Segoe UI", 12, "bold")
).pack()

tk.Label(
    main_frame,
    textvariable=trips_var,
    font=("Segoe UI", 22)
).pack()

tk.Label(
    main_frame,
    text="Average TTT",
    font=("Segoe UI", 12, "bold")
).pack()

tk.Label(
    main_frame,
    textvariable=ttt_var,
    font=("Segoe UI", 22)
).pack()

# STATUS

status = tk.StringVar(
    value="Ready"
)

status_bar = tk.Label(

    root,

    textvariable=status,

    anchor="w",

    bg="#003366",

    fg="white",

    padx=10

)

status_bar.pack(
    fill="x",
    side="bottom"
)

root.mainloop()