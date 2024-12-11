import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import threading
import os
from pathlib import Path

class AlgorandNodeMonitorGUI:
    def __init__(self, master):
        self.master = master
        master.title("Algorand Node Monitor")
        
        # Use Ubuntu default paths
        self.data_dir = '/var/lib/algorand'
        self.log_file = f'{self.data_dir}/node.log'

        # Create GUI elements
        self.setup_gui(master)
        
        # Initial status check
        self.check_node_status()
        self.poll_log()

    def setup_gui(self, master):
        """Setup all GUI elements."""
        # Variables
        self.status_var = tk.StringVar()
        
        # Create widgets
        self.status_label = ttk.Label(master, textvariable=self.status_var)        
        self.log_label = ttk.Label(master, text="Node Log:")
        self.start_button = ttk.Button(master, text="Start Node", command=self.start_node)
        self.stop_button = ttk.Button(master, text="Stop Node", command=self.stop_node)
        self.restart_button = ttk.Button(master, text="Restart Node", command=self.restart_node)
        self.log_text = tk.Text(master, height=20, width=80)
        self.scrollbar = ttk.Scrollbar(master, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=self.scrollbar.set)
        
        # Layout
        self.status_label.grid(row=0, column=0, columnspan=3, padx=10, pady=10, sticky="W")
        self.log_label.grid(row=1, column=0, columnspan=3, padx=10, sticky="W")
        self.log_text.grid(row=2, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
        self.scrollbar.grid(row=2, column=3, pady=10, sticky="ns")
        self.start_button.grid(row=3, column=0, padx=5, pady=10)
        self.stop_button.grid(row=3, column=1, padx=5, pady=10)
        self.restart_button.grid(row=3, column=2, padx=5, pady=10)
        
        # Configure grid
        master.grid_columnconfigure(0, weight=1)
        master.grid_rowconfigure(2, weight=1)

    def check_node_status(self):
        """Check if node is running."""
        try:
            result = subprocess.run(
                ['sudo', 'systemctl', 'status', 'algorand'],
                capture_output=True,
                text=True
            )
            if "active (running)" in result.stdout:
                self.status_var.set("Node Status: Running")
            else:
                self.status_var.set("Node Status: Stopped")
        except Exception as e:
            self.status_var.set(f"Node Status: Error checking status")
        
        # Schedule next check
        self.master.after(5000, self.check_node_status)

    def poll_log(self):
        """Poll and update log contents."""
        try:
            # Use sudo to read the log file
            result = subprocess.run(
                ['sudo', 'tail', '-n', '50', self.log_file],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, result.stdout)
                self.log_text.see(tk.END)
            else:
                self.log_text.delete(1.0, tk.END)
                self.log_text.insert(tk.END, "Error reading log file. Check permissions.")
                
        except Exception as e:
            self.log_text.delete(1.0, tk.END)
            self.log_text.insert(tk.END, f"Error: {str(e)}")
        
        # Schedule next poll
        self.master.after(5000, self.poll_log)

    def start_node(self):
        """Start the Algorand node."""
        try:
            subprocess.run(['sudo', 'systemctl', 'start', 'algorand'], check=True)
            messagebox.showinfo("Success", "Node start command issued")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start node: {str(e)}")

    def stop_node(self):
        """Stop the Algorand node."""
        try:
            subprocess.run(['sudo', 'systemctl', 'stop', 'algorand'], check=True)
            messagebox.showinfo("Success", "Node stop command issued")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to stop node: {str(e)}")

    def restart_node(self):
        """Restart the Algorand node."""
        try:
            subprocess.run(['sudo', 'systemctl', 'restart', 'algorand'], check=True)
            messagebox.showinfo("Success", "Node restart command issued")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to restart node: {str(e)}")

def main():
    # Check if running with sudo
    if os.geteuid() != 0:
        print("This script needs to be run with sudo privileges")
        exit(1)
        
    root = tk.Tk()
    app = AlgorandNodeMonitorGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
