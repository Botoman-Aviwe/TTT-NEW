import sys
import os
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

file_path = ""
status = None
minutes_var = None
trips_var = None
ttt_var = None

def browse_file():
    global file_path
    file_path = filedialog.askopenfilename(
        title="Select TTT Excel File",
        filetypes=[("Excel Files", "*.xlsx *.xls")]
    )
    if file_path:
        file_entry.config(state="normal")
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_path)
        file_entry.config(state="readonly")
        status.set("Excel file selected")

def process_file():
    global file_path
    if not file_path:
        messagebox.showerror("Error", "Please select an Excel file first.")
        return

    try:
        status.set("Processing...")
        progress.start()

        df = pd.read_excel(file_path)
        df["TimeDate"] = pd.to_datetime(df["TimeDate"])
        df = df.sort_values(["IdNumber", "TimeDate"])

        results = []
        for id_num, group in df.groupby("IdNumber"):
            arrive_time = None
            for _, row in group.iterrows():
                if row["Direction"] == "Arrive":
                    arrive_time = row["TimeDate"]
                elif row["Direction"] == "Depart" and arrive_time is not None:
                    minutes = (row["TimeDate"] - arrive_time).total_seconds() / 60
                    results.append({
                        "IdNumber": id_num,
                        "ArriveTime": arrive_time,
                        "DepartTime": row["TimeDate"],
                        "MinutesInTerminal": round(minutes, 2)
                    })
                    arrive_time = None

        result_df = pd.DataFrame(results)
        if result_df.empty:
            messagebox.showwarning("No Data", "No Arrive/Depart pairs were found.")
            status.set("No data found")
            progress.stop()
            return

        total_minutes = result_df["MinutesInTerminal"].sum()
        count_minutes = result_df["MinutesInTerminal"].count()
        TTT = total_minutes / count_minutes if count_minutes != 0 else 0

        fact_terminal = result_df.copy()
        fact_terminal["Date"] = fact_terminal["ArriveTime"].dt.date
        fact_terminal["Hour"] = fact_terminal["ArriveTime"].dt.hour
        fact_terminal["Shift"] = fact_terminal["Hour"].apply(
            lambda h: "Day Shift" if 6 <= h < 18 else "Night Shift"
        )

        summary_terminal = fact_terminal.groupby("IdNumber").agg(
            TotalMinutes=("MinutesInTerminal", "sum"),
            TripCount=("MinutesInTerminal", "count"),
            AvgMinutes=("MinutesInTerminal", "mean")
        ).reset_index()
        summary_terminal["TTT"] = summary_terminal["TotalMinutes"] / summary_terminal["TripCount"]

        output_folder = os.path.join(os.path.dirname(file_path), "Output")
        os.makedirs(output_folder, exist_ok=True)

        result_df.to_excel(os.path.join(output_folder, "Terminal_Turnaround.xlsx"), index=False)
        fact_terminal.to_excel(os.path.join(output_folder, "Fact_TerminalTurnaround.xlsx"), index=False)
        summary_terminal.to_excel(os.path.join(output_folder, "Summary_TerminalTurnaround.xlsx"), index=False)

        # Update KPI labels
        minutes_var.set(f"{total_minutes:.2f}")
        trips_var.set(str(count_minutes))
        ttt_var.set(f"{TTT:.2f} Minutes")

        messagebox.showinfo(
            "Processing Complete",
            f"Reports saved to:\n{output_folder}"
        )
        status.set("Completed Successfully")

    except Exception as e:
        messagebox.showerror("Error", str(e))
        status.set("Error occurred")
    finally:
        progress.stop()

# ====================================================
# GUI
# ====================================================
root = tk.Tk()
root.title("Terminal Turnaround Time System")
root.state("zoomed")  # Full screen
root.configure(bg="white")

# Header
header = tk.Frame(root, bg="#003366", height=80)
header.pack(fill="x")

logo_path = resource_path("images/logo.png")
if os.path.exists(logo_path):
    logo_img = Image.open(logo_path).resize((60, 60))
    logo_photo = ImageTk.PhotoImage(logo_img)
    logo_label = tk.Label(header, image=logo_photo, bg="#003366")
    logo_label.pack(side="left", padx=20)

title = tk.Label(
    header,
    text="Terminal Turnaround Time System",
    font=("Segoe UI", 28, "bold"),
    bg="#003366",
    fg="white"
)
title.pack(side="left", padx=20)

# Main Frame
main_frame = tk.Frame(root, bg="#F2F4F7")
main_frame.pack(fill="both", expand=True, padx=20, pady=20)

file_entry = tk.Entry(main_frame, font=("Segoe UI", 12), width=80, state="readonly")
file_entry.pack(pady=10)

browse_btn = tk.Button(
    main_frame,
    text="📂 Browse Excel File",
    font=("Segoe UI", 12, "bold"),
    bg="#0078D7",
    fg="white",
    width=25,
    height=2,
    command=browse_file
)
browse_btn.pack(pady=10)

process_btn = tk.Button(
    main_frame,
    text="▶ Process Data",
    font=("Segoe UI", 12, "bold"),
    bg="#009933",
    fg="white",
    width=25,
    height=2,
    command=process_file
)
process_btn.pack(pady=10)

# Progress Bar
progress = ttk.Progressbar(
    main_frame,
    orient="horizontal",
    length=500,
    mode="indeterminate"
)
progress.pack(pady=20)

# KPI Section
minutes_var = tk.StringVar(value="0")
trips_var = tk.StringVar(value="0")
ttt_var = tk.StringVar(value="0")

tk.Label(main_frame, text="Total Minutes", font=("Segoe UI", 12, "bold")).pack()
tk.Label(main_frame, textvariable=minutes_var, font=("Segoe UI", 22)).pack()

tk.Label(main_frame, text="Trips", font=("Segoe UI", 12, "bold")).pack()
tk.Label(main_frame, textvariable=trips_var, font=("Segoe UI", 22)).pack()

tk.Label(main_frame, text="Average TTT", font=("Segoe UI", 12, "bold")).pack()
tk.Label(main_frame, textvariable=ttt_var, font=("Segoe UI", 22)).pack()

# Status Bar
status = tk.StringVar()
status.set("Ready")
status_bar = tk.Label(
    root,
    textvariable=status,
    anchor="w",
    bg="#003366",
    fg="white",
    padx=10
)
status_bar.pack(fill="x", side="bottom")

# Footer
footer = tk.Label(
    root,
    text="© 2026 Transnet Port Terminals | MIS Department | Developed by Aviwe Botoman",
    bg="#003366",
    fg="white",
    font=("Segoe UI", 10)
)
footer.pack(fill="x")

root.mainloop()


