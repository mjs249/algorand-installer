#!/bin/bash
source venv/bin/activate
python3 -c "from gui.installer_gui import InstallerGUI; InstallerGUI().run()"
