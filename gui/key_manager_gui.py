import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import subprocess

class AlgorandKeyManagerGUI:
    def __init__(self, master):
        self.master = master
        master.title("Algorand Key Manager")

        self.key_list = tk.Listbox(master, height=10, width=50)
        self.generate_button = ttk.Button(master, text="Generate Key", command=self.generate_key)
        self.sign_button = ttk.Button(master, text="Sign Transaction", command=self.sign_transaction)

        self.key_list.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
        self.generate_button.grid(row=1, column=0, padx=5, pady=10)
        self.sign_button.grid(row=1, column=1, padx=5, pady=10)

        self.update_key_list()

    def update_key_list(self):
        result = subprocess.run(["goal", "account", "list"], capture_output=True, text=True)
        keys = result.stdout.strip().split("\n")
        self.key_list.delete(0, tk.END)
        for key in keys:
            self.key_list.insert(tk.END, key)

    def generate_key(self):
        result = subprocess.run(["goal", "account", "new"], capture_output=True, text=True)
        address = result.stdout.strip().split(":")[1].strip()
        messagebox.showinfo("New Account", f"Generated new account: {address}")
        self.update_key_list()

    def sign_transaction(self):
        key = self.key_list.get(tk.ACTIVE)
        if not key:
            messagebox.showerror("Error", "Please select an account.")
            return

        txn_file = simpledialog.askstring("Sign Transaction", "Enter path to transaction file:")
        if not txn_file:
            return

        try:
            subprocess.run(["goal", "clerk", "sign", "-i", txn_file, "-a", key], check=True)
            messagebox.showinfo("Transaction Signed", "Transaction signed successfully!")
        except subprocess.CalledProcessError as e:
            messagebox.showerror("Error", f"Failed to sign transaction: {e}")

if __name__ == "__main__": 
    root = tk.Tk()
    app = AlgorandKeyManagerGUI(root)
    root.mainloop()
