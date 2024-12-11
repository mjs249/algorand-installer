import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess
import os
from datetime import datetime
from pathlib import Path

class AlgorandKeyManagerGUI:
    DEFAULT_DATA_DIR = '/var/lib/algorand'  # Match installer constant

    def __init__(self, master):
        self.master = master
        master.title("Algorand Key Manager")

        # Get the real user's home directory and username
        self.real_user = os.environ.get('SUDO_USER')
        if not self.real_user:
            messagebox.showerror("Error", "This script must be run with sudo")
            master.destroy()
            return

        # Verify data directory
        data_dir = Path(self.DEFAULT_DATA_DIR)
        if not data_dir.exists():
            messagebox.showerror("Error", f"Data directory {self.DEFAULT_DATA_DIR} not found!")
            master.destroy()
            return

        # Create main frame
        self.main_frame = ttk.Frame(master)
        self.main_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Create widgets
        self.create_widgets()
        
        # Initialize wallet
        self.initialize_wallet()
        
        # Initial update
        self.update_key_list()

    def create_widgets(self):
        # Key list with scrollbar
        list_frame = ttk.Frame(self.main_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.key_list = tk.Listbox(list_frame, height=10, width=60)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.key_list.yview)
        self.key_list.configure(yscrollcommand=scrollbar.set)
        
        self.key_list.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Status label
        self.status_var = tk.StringVar(value="Status: Ready")
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var)
        self.status_label.pack(fill=tk.X, pady=(0, 5))

        # Buttons frame
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.wallet_button = ttk.Button(button_frame, text="Create Wallet", command=self.create_wallet)
        self.generate_button = ttk.Button(button_frame, text="Generate Key", command=self.generate_key)
        self.partkey_button = ttk.Button(button_frame, text="Generate Participation Key", command=self.generate_partkey)
        self.list_partkey_button = ttk.Button(button_frame, text="List Participation Keys", command=self.list_partkeys)
        self.refresh_button = ttk.Button(button_frame, text="Refresh", command=self.update_key_list)

        self.wallet_button.pack(side=tk.LEFT, padx=5)
        self.generate_button.pack(side=tk.LEFT, padx=5)
        self.partkey_button.pack(side=tk.LEFT, padx=5)
        self.list_partkey_button.pack(side=tk.LEFT, padx=5)
        self.refresh_button.pack(side=tk.LEFT, padx=5)

    def run_goal_command(self, args):
        """Run goal command with proper permissions."""
        try:
            # Use process substitution to preserve environment
            env = os.environ.copy()
            
            # Build the goal command
            cmd = ['sudo', '-u', 'algorand', '-E', 'goal'] + args + ['-d', self.DEFAULT_DATA_DIR]
            
            # Update status and ensure window updates
            self.status_var.set(f"Status: Running command...")
            self.master.update()
            
            # Run the command
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Update status and ensure window updates
            self.status_var.set("Status: Ready")
            self.master.update()
            
            if result.returncode != 0:
                error_msg = result.stderr or "Unknown error"
                raise Exception(f"Command failed: {error_msg}")
            
            # Force focus back to main window
            self.master.lift()
            self.master.focus_force()
            
            return result
            
        except Exception as e:
            self.status_var.set("Status: Error")
            self.master.update()
            messagebox.showerror("Error", str(e), parent=self.master)
            return None

    @staticmethod
    def fix_x11_permissions():
        """Fix X11 permissions for the real user."""
        real_user = os.environ.get('SUDO_USER')
        if real_user:
            try:
                subprocess.run(['xhost', f"+si:localuser:{real_user}"], check=True)
            except Exception as e:
                print(f"Warning: Could not set X11 permissions: {e}")

    def initialize_wallet(self):
        """Check for and initialize wallet if needed."""
        result = self.run_goal_command(['wallet', 'list'])
        if result and "No wallets found" in result.stdout:
            if messagebox.askyesno("No Wallet Found", 
                                 "No wallets found. Would you like to create a default wallet?",
                                 parent=self.master):
                self.create_wallet()
                self.master.focus_force()  # Return focus to main window
                self.master.update()

    def create_wallet(self):
        """Create a new wallet."""
        try:
            name = simpledialog.askstring("Wallet Name", 
                                        "Enter wallet name (default: unencrypted-default-wallet):",
                                        initialvalue="unencrypted-default-wallet",
                                        parent=self.master)
            if not name:
                self.master.focus_force()  # Return focus if canceled
                self.master.update()
                return
                
            result = self.run_goal_command(['wallet', 'new', name])
            if result and result.stdout:
                messagebox.showinfo("Success", f"Created new wallet: {name}", 
                                  parent=self.master)
                self.update_key_list()
            self.master.focus_force()  # Return focus after creation
            self.master.update()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create wallet: {str(e)}", 
                               parent=self.master)
            self.master.focus_force()  # Return focus after error
            self.master.update()

    def update_key_list(self):
        """Update the list of accounts."""
        self.key_list.delete(0, tk.END)
        
        # First check for wallet
        wallet_result = self.run_goal_command(['wallet', 'list'])
        if wallet_result and "No wallets found" in wallet_result.stdout:
            self.key_list.insert(tk.END, "No wallets found. Create a wallet first.")
            return
            
        # Then list accounts if wallet exists
        result = self.run_goal_command(['account', 'list'])
        if result and result.stdout:
            if not result.stdout.strip():
                self.key_list.insert(tk.END, "No accounts found. Generate a new key.")
            else:
                for line in result.stdout.strip().split('\n'):
                    if line:  # Skip empty lines
                        self.key_list.insert(tk.END, line)

    def generate_key(self):
        """Generate a new account."""
        try:
            # Check for wallet first
            wallet_result = self.run_goal_command(['wallet', 'list'])
            if wallet_result and "No wallets found" in wallet_result.stdout:
                messagebox.showwarning("Warning", "Please create a wallet first",
                                     parent=self.master)
                return
                
            result = self.run_goal_command(['account', 'new'])
            if result and result.stdout:
                # Look for address in output
                for line in result.stdout.split('\n'):
                    if 'Created new account with address' in line:
                        address = line.split('address')[-1].strip()
                        messagebox.showinfo("Success", f"Generated new account: {address}",
                                          parent=self.master)
                        self.update_key_list()
                        return
            raise Exception("Could not parse new account address")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate key: {str(e)}",
                               parent=self.master)

    def generate_partkey(self):
        """Generate a participation key."""
        try:
            # Get selected account
            selection = self.key_list.curselection()
            if not selection:
                messagebox.showwarning("Warning", "Please select an account first",
                                     parent=self.master)
                return
                
            account = self.key_list.get(selection[0]).split(' ')[0]
            
            # Get round information
            first_round = simpledialog.askinteger("Input", "Enter first valid round:", 
                                                initialvalue=1,
                                                parent=self.master)
            if first_round is None:
                return
                
            last_round = simpledialog.askinteger("Input", "Enter last valid round:", 
                                                initialvalue=first_round + 3000000,
                                                parent=self.master)
            if last_round is None:
                return
                
            if last_round - first_round > 3000000:
                if not messagebox.askyesno("Warning", 
                    "The range exceeds recommended 3,000,000 rounds. Continue anyway?",
                    parent=self.master):
                    return
            
            # Generate participation key
            result = self.run_goal_command([
                'account', 'addpartkey',
                '-a', account,
                '--roundFirstValid', str(first_round),
                '--roundLastValid', str(last_round)
            ])
            
            if result and result.stdout:
                messagebox.showinfo("Success", 
                    "Participation key generated successfully!\n\n" +
                    "Note: It will take 320 rounds for changes to take effect.",
                    parent=self.master)
            
        except Exception as e:
            messagebox.showerror("Error", 
                f"Failed to generate participation key: {str(e)}",
                parent=self.master)

    def list_partkeys(self):
        """List all participation keys."""
        try:
            result = self.run_goal_command(['account', 'listpartkeys'])
            if result:
                dialog = tk.Toplevel(self.master)
                dialog.title("Participation Keys")
                
                # Add info label
                info_label = ttk.Label(dialog, text="Note: Changes to participation keys take 320 rounds to take effect.", 
                                     wraplength=500)
                info_label.pack(pady=5)
                
                text = tk.Text(dialog, height=20, width=80)
                scrollbar = ttk.Scrollbar(dialog, orient="vertical", 
                                        command=text.yview)
                text.configure(yscrollcommand=scrollbar.set)
                
                text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                text.insert(tk.END, result.stdout)
                text.config(state='disabled')
                
        except Exception as e:
            messagebox.showerror("Error", 
                f"Failed to list participation keys: {str(e)}",
                parent=self.master)

def main():
    # Check if running with sudo
    if os.geteuid() != 0:
        print("This script needs to be run with sudo privileges.")
        print(f"Usage: sudo python3 {os.path.basename(__file__)}")
        exit(1)

    # Fix X11 permissions before creating the window
    AlgorandKeyManagerGUI.fix_x11_permissions()
    
    root = tk.Tk()
    app = AlgorandKeyManagerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
