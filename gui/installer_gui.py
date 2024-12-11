# gui/installer_gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import queue
from pathlib import Path
from typing import Optional
from .settings_dialog import AdvancedSettingsDialog

class InstallerGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Algorand Node Installer")
        self.root.geometry("700x500")
        
        # Setup queue for thread-safe GUI updates
        self.queue = queue.Queue()
        
        self._setup_variables()
        self._setup_gui()
        
    def _setup_variables(self):
        """Initialize GUI variables."""
        self.network_var = tk.StringVar(value="mainnet")
        self.relay_var = tk.BooleanVar(value=False)
        self.archival_var = tk.BooleanVar(value=False)
        self.telemetry_var = tk.BooleanVar(value=False)
        self.install_dir_var = tk.StringVar(value=str(Path.home() / 'algorand'))
        
    def _setup_gui(self):
        """Setup the main GUI elements."""
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Header
        header = ttk.Label(
            self.main_frame,
            text="Algorand Node Installation",
            font=('Helvetica', 16, 'bold')
        )
        header.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Network selection
        self._add_network_selection()
        
        # Node configuration
        self._add_node_configuration()
        
        # Installation directory
        self._add_install_directory()
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(
            self.main_frame,
            length=400,
            mode='determinate',
            variable=self.progress_var
        )
        self.progress.grid(row=4, column=0, columnspan=2, pady=(20, 10))
        
        # Status message
        self.status_var = tk.StringVar(value="Ready to install")
        status = ttk.Label(
            self.main_frame,
            textvariable=self.status_var
        )
        status.grid(row=5, column=0, columnspan=2)
        
        # Buttons
        button_frame = ttk.Frame(self.main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(
            button_frame,
            text="Advanced Settings",
            command=self.show_advanced_settings
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            button_frame,
            text="Install",
            command=self.start_installation
        ).grid(row=0, column=1, padx=5)
        
    def _add_network_selection(self):
        """Add network selection controls."""
        network_frame = ttk.LabelFrame(
            self.main_frame,
            text="Network Selection",
            padding="10"
        )
        network_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        for i, network in enumerate(['MainNet', 'TestNet', 'BetaNet']):
            ttk.Radiobutton(
                network_frame,
                text=network,
                value=network.lower(),
                variable=self.network_var
            ).grid(row=0, column=i, padx=10)
            
    def _add_node_configuration(self):
        """Add node configuration controls."""
        config_frame = ttk.LabelFrame(
            self.main_frame,
            text="Node Configuration",
            padding="10"
        )
        config_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Checkbutton(
            config_frame,
            text="Setup as relay node",
            variable=self.relay_var,
            command=self._on_relay_change
        ).grid(row=0, column=0, padx=10)
        
        ttk.Checkbutton(
            config_frame,
            text="Enable archival mode",
            variable=self.archival_var
        ).grid(row=0, column=1, padx=10)
        
        ttk.Checkbutton(
            config_frame,
            text="Enable telemetry",
            variable=self.telemetry_var
        ).grid(row=0, column=2, padx=10)
        
    def _add_install_directory(self):
        """Add installation directory controls."""
        dir_frame = ttk.LabelFrame(
            self.main_frame,
            text="Installation Directory",
            padding="10"
        )
        dir_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Entry(
            dir_frame,
            textvariable=self.install_dir_var,
            width=50
        ).grid(row=0, column=0, padx=5)
        
        ttk.Button(
            dir_frame,
            text="Browse",
            command=self._browse_directory
        ).grid(row=0, column=1, padx=5)
        
    def _on_relay_change(self):
        """Handle relay node checkbox changes."""
        if self.relay_var.get():
            self.archival_var.set(True)  # Relay nodes must be archival
            
    def _browse_directory(self):
        """Show directory selection dialog."""
        from tkinter import filedialog
        directory = filedialog.askdirectory(
            initialdir=self.install_dir_var.get()
        )
        if directory:
            self.install_dir_var.set(directory)
            
    def show_advanced_settings(self):
        """Show advanced settings dialog."""
        from utils.config_manager import AlgorandConfig
        
        config_manager = AlgorandConfig(
            Path(self.install_dir_var.get()) / 'data',
            is_relay=self.relay_var.get()
        )
        
        def save_settings(updates):
            config_manager.update_config(updates)
            config_manager.save_config()
            
        AdvancedSettingsDialog(
            self.root,
            config_manager.get_config(),
            save_settings
        )
        
    def start_installation(self):
        """Begin the installation process."""
        # Disable interface
        self._set_interface_state('disabled')
        
        # Start installation in separate thread
        thread = threading.Thread(target=self._run_installation)
        thread.daemon = True
        thread.start()
        
        # Start checking queue for updates
        self.root.after(100, self._check_queue)
        
    def _set_interface_state(self, state: str):
        """Enable/disable interface elements."""
        for child in self.main_frame.winfo_children():
            try:
                child['state'] = state
            except Exception:
                pass
                
    def _run_installation(self):
        """Run the actual installation process."""
        try:
            from main import AlgorandInstaller
            
            installer = AlgorandInstaller()
            installer.config.update({
                'install_dir': Path(self.install_dir_var.get()),
                'data_dir': Path(self.install_dir_var.get()) / 'data',
                'network': self.network_var.get(),
                'is_relay': self.relay_var.get(),
                'is_archival': self.archival_var.get(),
                'enable_telemetry': self.telemetry_var.get()
            })
            
            success = installer.run_installation()
            
            if success:
                self.queue.put(('done', None))
            else:
                self.queue.put(('error', "Installation failed. Check logs for details."))
                
        except Exception as e:
            self.queue.put(('error', str(e)))
            
    def _check_queue(self):
        """Check for updates from installation thread."""
        try:
            while True:
                msg = self.queue.get_nowait()
                if msg[0] == 'progress':
                    self.progress_var.set(msg[1])
                    self.status_var.set(msg[2])
                elif msg[0] == 'error':
                    messagebox.showerror("Installation Error", msg[1])
                    self._set_interface_state('normal')
                    return
                elif msg[0] == 'done':
                    messagebox.showinfo("Success", 
                                      "Algorand node installed successfully!")
                    self._set_interface_state('normal')
                    return
        except queue.Empty:
            self.root.after(100, self._check_queue)
            
    def run(self):
        """Start the GUI."""
        self.root.mainloop()
