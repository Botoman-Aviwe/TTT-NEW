import os
import subprocess
import pandas as pd
import tkinter as tk
import traceback
from io import StringIO

from tkinter import ttk
from tkinter import messagebox

from tkcalendar import DateEntry


# ======================================================
# CONFIG
# ======================================================
REPORT_URL = "https://10.39.215.77/report"

# ======================================================
# RETRIEVE REPORT
# ======================================================



def get_report():

    username = username_var.get().strip()
    password = password_var.get().strip()

    if not username:
        raise Exception("Username is required")

    if not password:
        raise Exception("Password is required")

    from_date = (
        start_date.get_date().strftime("%Y-%m-%d")
        + "T"
        + start_time.get()
    )

    to_date = (
        end_date.get_date().strftime("%Y-%m-%d")
        + "T"
        + end_time.get()
    )

    post_data = (
        f"reportName=VisitorsLog Per Area"
        f"&@FromDate={from_date}"
        f"&@ToDate={to_date}"
        f"&@IncludePhotos=0"
    )

    cmd = [
        "curl.exe",
        "-k",
        "-u",
        f"{username}:{password}",
        "-X",
        "POST",
        REPORT_URL,
        "--data-raw",
        post_data
    ]

    print(cmd)

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    print("RETURN CODE:", result.returncode)
    print("STDERR:", result.stderr)

    if result.returncode != 0:
        raise Exception(result.stderr)

    html = result.stdout

    print("HTML LENGTH:", len(html))

    tables = pd.read_html(
        StringIO(html)
    )

    print(
        f"TABLES FOUND: {len(tables)}"
    )

    return tables[0]
# ======================================================
# PROCESS TTT
# ======================================================



def process_ttt():

    try:

        print("========== STARTING ==========")

        progress.start()

        status_var.set(
            "Retrieving report..."
        )

        source_df = get_report()

        print("========== DATA RETRIEVED ==========")

        print(source_df.columns.tolist())

        print(source_df.head())
        print(source_df.columns.tolist())

    
        source_df["TimeDate"] = pd.to_datetime(
        source_df["TimeDate"],
        format="%m/%d/%Y %I:%M:%S %p")

        results = []

        for id_num, group in source_df.groupby(
                "IdNumber"):

            arrival = None

            for _, row in group.iterrows():

                if row["Direction"] == "Arrive":

                    arrival = row["TimeDate"]

                elif (
                    row["Direction"] == "Depart"
                    and arrival is not None
                ):

                    minutes = (

                        row["TimeDate"]
                        -
                        arrival

                    ).total_seconds() / 60

                    results.append(

                        {

                            "IdNumber":
                            id_num,

                            "ArriveTime":
                            arrival,

                            "DepartTime":
                            row["TimeDate"],

                            "MinutesInTerminal":
                            round(
                                minutes,
                                2
                            )

                        }

                    )

                    arrival = None
        result_df = pd.DataFrame(results)

        if result_df.empty:
            raise Exception(
                "No Arrive/Depart pairs found."
            )

        output_folder = "Output"
        os.makedirs(output_folder, exist_ok=True)

        source_df.to_excel(
            os.path.join(
                output_folder,
                "Raw_Report.xlsx"
            ),
            index=False
        )

        total_minutes = result_df["MinutesInTerminal"].sum()

        total_trips = len(result_df)

        average_ttt = total_minutes / total_trips

        minutes_var.set(f"{total_minutes:,.2f}")
        trips_var.set(str(total_trips))
        avg_var.set(f"{average_ttt:.2f}")

        root.update_idletasks()

        result_df.to_excel(
            os.path.join(output_folder, "Truck_Turnaround.xlsx"),
            index=False
        )

        progress.stop()
        status_var.set("Completed")

        messagebox.showinfo(
            "Success",
            f"""
Total Minutes : {total_minutes:,.2f}

Trips : {total_trips}

Average TTT : {average_ttt:.2f}

Output Folder:
{output_folder}
"""
    )

    except Exception as ex:

        traceback.print_exc()

        progress.stop()

        status_var.set(
            "Error"
        )

        messagebox.showerror(
            "Error",
            str(ex)
        )

# ======================================================
# GUI
# ======================================================

root = tk.Tk()

root.title(
    "Truck Turnaround Time"
)

root.geometry(
    "1200x800"
)

root.configure(
    bg="white"
)

# ======================================================
# HEADER
# ======================================================

header = tk.Frame(
    root,
    bg="#003366",
    height=70
)

header.pack(
    fill="x"
)

title = tk.Label(

    header,

    text="Truck Turnaround Time System",

    bg="#003366",

    fg="white",

    font=(

        "Segoe UI",

        22,

        "bold"

    )

)

title.pack(
    pady=15
)

# ======================================================
# LEFT PANEL
# ======================================================

left = tk.LabelFrame(

    root,

    text="Versatech Parameters",

    padx=10,

    pady=10

)

left.pack(

    side="left",

    fill="y",

    padx=10,

    pady=10

)

# USERNAME

tk.Label(
    left,
    text="Username"
).pack(
    anchor="w"
)

username_var = tk.StringVar()

tk.Entry(

    left,

    textvariable=username_var,

    width=30

).pack(
    pady=3
)

# PASSWORD

tk.Label(
    left,
    text="Password"
).pack(
    anchor="w"
)

password_var = tk.StringVar()

tk.Entry(

    left,

    textvariable=password_var,

    show="*",

    width=30

).pack(
    pady=3
)

# START DATE

tk.Label(
    left,
    text="Start Date"
).pack(
    anchor="w"
)

start_date = DateEntry(

    left,

    width=20,

    date_pattern="yyyy-mm-dd"

)

start_date.pack(
    pady=3
)

# START TIME

tk.Label(
    left,
    text="Start Time"
).pack(
    anchor="w"
)

start_time = ttk.Combobox(

    left,

    width=18,

    state="readonly"

)

start_time["values"] = [

    "00:00",
    "01:00",
    "02:00",
    "03:00",
    "04:00",
    "05:00",
    "06:00",
    "07:00",
    "08:00",
    "09:00",
    "10:00",
    "11:00",
    "12:00",
    "13:00",
    "14:00",
    "15:00",
    "16:00",
    "17:00",
    "18:00",
    "19:00",
    "20:00",
    "21:00",
    "22:00",
    "23:00"

]

start_time.set(
    "06:00"
)

start_time.pack(
    pady=3
)

# END DATE

tk.Label(
    left,
    text="End Date"
).pack(
    anchor="w"
)

end_date = DateEntry(

    left,

    width=20,

    date_pattern="yyyy-mm-dd"

)

end_date.pack(
    pady=3
)

# END TIME

tk.Label(
    left,
    text="End Time"
).pack(
    anchor="w"
)

end_time = ttk.Combobox(

    left,

    width=18,

    state="readonly"

)

end_time["values"] = start_time["values"]

end_time.set(
    "06:00"
)

end_time.pack(
    pady=3
)

# PROCESS BUTTON

tk.Button(

    left,

    text="Retrieve & Process",

    bg="#008000",

    fg="white",

    height=2,

    command=process_ttt

).pack(

    fill="x",

    pady=15

)

# ======================================================
# RIGHT PANEL
# ======================================================

right = tk.Frame(
    root
)

right.pack(
    fill="both",
    expand=True,
    padx=10,
    pady=10
)

progress = ttk.Progressbar(

    right,

    mode="indeterminate",

    length=500

)

progress.pack(
    pady=20
)

minutes_var = tk.StringVar(
    value="0"
)

trips_var = tk.StringVar(
    value="0"
)

avg_var = tk.StringVar(
    value="0"
)

kpi1 = tk.Label(

    right,

    textvariable=minutes_var,

    font=(

        "Segoe UI",

        32,

        "bold"

    )

)

kpi1.pack()

tk.Label(

    right,

    text="Total Minutes",

    font=(

        "Segoe UI",

        12

    )

).pack()

kpi2 = tk.Label(

    right,

    textvariable=trips_var,

    font=(

        "Segoe UI",

        32,

        "bold"

    )

)

kpi2.pack()

tk.Label(

    right,

    text="Trips",

    font=(

        "Segoe UI",

        12

    )

).pack()

kpi3 = tk.Label(

    right,

    textvariable=avg_var,

    font=(

        "Segoe UI",

        32,

        "bold"

    )

)

kpi3.pack()

tk.Label(

    right,

    text="Average TTT",

    font=(

        "Segoe UI",

        12

    )

).pack()

# STATUS

status_var = tk.StringVar(
    value="Ready"
)

footer = tk.Frame(
    root,
    bg="#003366",
    height=25
)

footer.pack(
    fill="x",
    side="bottom"
)

status_bar = tk.Label(
    footer,
    textvariable=status_var,
    bg="#003366",
    fg="white",
    anchor="w"
)

status_bar.pack(
    side="left",
    padx=10
)

developer_label = tk.Label(
    footer,
    text="Developed by Aviwe Botoman | YPT MIS | Transnet Port Terminals",
    bg="#003366",
    fg="white",
    font=("Segoe UI", 9, "italic")
)

developer_label.pack(
    side="right",
    padx=10
)

root.mainloop()
