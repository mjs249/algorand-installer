import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import threading
import os

class AlgorandNodeMonitorGUI:
    def __init__(self, master):
        self.master = master
        master.title("Algorand Node Monitor")

        self.status_var = tk.StringVar()
        self.log_text = tk.Text(master, height=20, width=80)

        self.status_label = ttk.Label(master, textvariable=self.status_var)        
        self.log_label = ttk.Label(master, text="Node Log:")
        self.start_button = ttk.Button(master, text="Start Node", command=self.start_node)
        self.stop_button = ttk.Button(master, text="Stop Node", command=self.stop_node)
        self.restart_button = ttk.Button(master, text="Restart Node", command=self.restart_node)
        self.log_text = tk.Text(master, height=20, width=80)

        self.status_label.grid(row=0, column=0, padx=10, pady=10, sticky="W")
        self.log_label.grid(row=1, column=0, padx=10, sticky="W") 
        self.log_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.start_button.grid(row=3, column=0, padx=5, pady=10)
        self.stop_button.grid(row=3, column=1, padx=5, pady=10)
        self.restart_button.grid(row=3, column=2, padx=5, pady=10)

        self.log_file = os.path.expanduser("~/node/data/node.log")
        self.poll_log()

    def poll_log(self):
        with open(self.log_file, "r") as f:
            log = f.read()
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, log)
            self.log_text.see(tk.END)

        self.master.after(5000, self.poll_log)  # Poll every 5 seconds

    def start_node(self):
        subprocess.Popen(["goal", "node", "start"])
        self.status_var.set("Node status: Running")

    def stop_node(self):
        subprocess.Popen(["goal", "node", "stop"])
        self.status_var.set("Node status: Stopped")

    def restart_node(self):
        subprocess.Popen(["goal", "node", "restart"])
        self.status_var.set("Node status: Restarted")

if __name__ == "__main__":
    root = tk.Tk()
    app = AlgorandNodeMonitorGUI(root)
    root.mainloop()
