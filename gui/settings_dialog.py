# gui/settings_dialog.py
import tkinter as tk
from tkinter import ttk
from typing import Dict, Any, Callable

class AdvancedSettingsDialog:
    def __init__(self, parent, config: Dict[str, Any], on_save: Callable[[Dict[str, Any]], None]):
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Advanced Node Settings")
        self.dialog.geometry("600x400")
        self.config = config
        self.on_save = on_save
        self._setup_gui()
        
    def _setup_gui(self):
        """Setup the settings dialog GUI."""
        # Create notebook for tabs
        notebook = ttk.Notebook(self.dialog)
        notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Basic settings tab
        basic_frame = ttk.Frame(notebook)
        notebook.add(basic_frame, text='Basic Settings')
        
        # Network settings tab
        network_frame = ttk.Frame(notebook)
        notebook.add(network_frame, text='Network')
        
        # Performance settings tab
        perf_frame = ttk.Frame(notebook)
        notebook.add(perf_frame, text='Performance')
        
        # API settings tab
        api_frame = ttk.Frame(notebook)
        notebook.add(api_frame, text='API')
        
        # Add settings to basic tab
        self._add_basic_settings(basic_frame)
        self._add_network_settings(network_frame)
        self._add_performance_settings(perf_frame)
        self._add_api_settings(api_frame)
        
        # Add save button
        save_btn = ttk.Button(
            self.dialog,
            text="Save Settings",
            command=self._save_settings
        )
        save_btn.pack(pady=10)
        
    def _add_basic_settings(self, parent):
        """Add basic node settings."""
        settings = [
            ("Archival Mode", "Archival", "boolean"),
            ("Base Logger Level", "BaseLoggerDebugLevel", "integer"),
            ("Enable Metrics", "EnableMetricReporting", "boolean"),
            ("Enable Telemetry", "EnableTelemetry", "boolean"),
        ]
        
        self._create_settings_group(parent, "Basic Settings", settings)
        
    def _add_network_settings(self, parent):
        """Add network-related settings."""
        settings = [
            ("Gossip Fanout", "GossipFanout", "integer"),
            ("Incoming Connections Limit", "IncomingConnectionsLimit", "integer"),
            ("Enable Block Service", "EnableBlockService", "boolean"),
            ("Enable Ledger Service", "EnableLedgerService", "boolean"),
        ]
        
        self._create_settings_group(parent, "Network Settings", settings)
        
    def _add_performance_settings(self, parent):
        """Add performance-related settings."""
        settings = [
            ("Transaction Pool Size", "TxPoolSize", "integer"),
            ("Catchup Parallel Blocks", "CatchupParallelBlocks", "integer"),
            ("Deadlock Detection", "DeadlockDetection", "integer"),
        ]
        
        self._create_settings_group(parent, "Performance Settings", settings)
        
    def _add_api_settings(self, parent):
        """Add API-related settings."""
        settings = [
            ("Enable Developer API", "EnableDeveloperAPI", "boolean"),
            ("Enable API Auth", "EnableAPIAuth", "boolean"),
            ("REST Read Timeout", "RestReadTimeoutSeconds", "integer"),
            ("REST Write Timeout", "RestWriteTimeoutSeconds", "integer"),
        ]
        
        self._create_settings_group(parent, "API Settings", settings)
        
    def _create_settings_group(self, parent, title: str, settings: list):
        """Create a group of settings controls."""
        frame = ttk.LabelFrame(parent, text=title, padding=10)
        frame.pack(fill='x', padx=10, pady=5)
        
        self.variables = {}
        
        for i, (label, key, type_) in enumerate(settings):
            ttk.Label(frame, text=label).grid(row=i, column=0, sticky='w', padx=5, pady=2)
            
            if type_ == "boolean":
                var = tk.BooleanVar(value=self.config.get(key, False))
                widget = ttk.Checkbutton(frame, variable=var)
            else:  # integer
                var = tk.StringVar(value=str(self.config.get(key, 0)))
                widget = ttk.Entry(frame, textvariable=var, width=15)
                
            widget.grid(row=i, column=1, padx=5, pady=2)
            self.variables[key] = (var, type_)
            
    def _save_settings(self):
        """Save the settings and close dialog."""
        updates = {}
        for key, (var, type_) in self.variables.items():
            if type_ == "boolean":
                updates[key] = var.get()
            else:  # integer
                try:
                    updates[key] = int(var.get())
                except ValueError:
                    continue
        
        self.on_save(updates)
        self.dialog.destroy()
