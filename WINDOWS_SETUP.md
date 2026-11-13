# Windows Setup Guide

Since you're running Windows, here are the specific commands to get the MDR Current Data Logger running.

## Quick Setup (Windows)

### 1. Verify Python Installation
Open PowerShell or Command Prompt and run:
```powershell
python --version
```
You should see: `Python 3.12.x` or higher

### 2. Navigate to Project Directory
```powershell
cd "C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger"
```

### 3. Create Virtual Environment (Optional but Recommended)
```powershell
python -m venv venv
```

### 4. Activate Virtual Environment
**IMPORTANT: This is the Windows command (NOT the Linux/macOS command)**
```powershell
venv\Scripts\activate
```

You should see `(venv)` appear at the beginning of your PowerShell prompt when activated.

To deactivate later:
```powershell
deactivate
```

### 5. Install Dependencies
```powershell
pip install -r requirements.txt
```

This installs all required packages:
- PyQt6
- pycomm3
- pyqtgraph
- pandas
- numpy

### 6. Run the Application
```powershell
python mdr_logger.py
```

The application window should open immediately.

## Troubleshooting Windows Issues

### "python is not recognized"
Python isn't in your PATH. Solutions:
1. Use full path: `C:\Python312\python.exe --version`
2. Reinstall Python and check "Add Python to PATH" during installation
3. Use `py` instead: `py --version`

### "venv\Scripts\activate" produces error
Make sure you're using backslashes `\` not forward slashes `/`:
- ✅ Correct: `venv\Scripts\activate`
- ❌ Wrong: `venv/Scripts/activate`

### "Cannot find module pyqtgraph" or similar
Make sure virtual environment is activated first:
```powershell
# Check if activated (should see (venv) in prompt)
venv\Scripts\activate

# Then install
pip install -r requirements.txt
```

### Application window doesn't appear
Try running with verbose output:
```powershell
python -u mdr_logger.py
```

## Common Windows Commands

### File/Directory Navigation
```powershell
# List files
Get-ChildItem

# Change directory
cd path\to\directory

# Create folder
New-Item -ItemType Directory -Path foldername

# Delete folder
Remove-Item -Recurse -Force foldername
```

### Package Management
```powershell
# List installed packages
pip list

# Upgrade pip
python -m pip install --upgrade pip

# Install specific version
pip install pyqtgraph==0.13.3

# Uninstall package
pip uninstall packagename
```

### Virtual Environment
```powershell
# Create
python -m venv venv

# Activate
venv\Scripts\activate

# Deactivate
deactivate

# Delete (just remove folder)
Remove-Item -Recurse -Force venv
```

## Windows PowerShell vs Command Prompt

The commands work in both, but PowerShell is recommended:

**PowerShell:**
```powershell
venv\Scripts\activate
python mdr_logger.py
```

**Command Prompt (cmd.exe):**
```cmd
venv\Scripts\activate
python mdr_logger.py
```

Both work identically for these commands.

## VS Code Integration (Optional)

If using VS Code, you can make it easier:

1. **Open folder in VS Code:**
   ```powershell
   code C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger
   ```

2. **Select Python interpreter:**
   - Press `Ctrl + Shift + P`
   - Type "Python: Select Interpreter"
   - Choose `./venv/Scripts/python.exe`

3. **Run application:**
   - Press `Ctrl + F5` or use Run menu

4. **Terminal in VS Code:**
   - `Ctrl + ~` opens integrated terminal
   - It will automatically activate venv when opened in project folder

## After Installation

Once everything is running:

1. **Connect to PLC:**
   - Enter your PLC IP address (e.g., 192.168.1.100)
   - Click "Connect"
   - Status indicator should turn green

2. **View data:**
   - Go to "Live Trends" tab
   - Real-time graphs should update

3. **Next steps:**
   - See [QUICKSTART.md](QUICKSTART.md) for first use
   - See [README.md](README.md) for complete guide

## Getting Help

If you encounter issues:

1. Check logs: `type %USERPROFILE%\.mdr_logger\mdr_logger.log`
2. Check [README.md](README.md) troubleshooting section
3. Verify Python version: `python --version`
4. Verify dependencies: `pip list`

## Windows Path Notes

- Home directory: `C:\Users\YourUsername` or `%USERPROFILE%`
- Configuration saved to: `~/.mdr_logger/` (which is `%USERPROFILE%\.mdr_logger\`)
- This is normal Windows behavior - the `.` at the start makes it hidden

To see hidden files in Windows Explorer:
- View menu → Options → Change folder and search options → View tab → Show hidden files

## Summary

**Windows activation command:**
```powershell
venv\Scripts\activate
```

**NOT:**
```powershell
source venv/bin/activate    # This is for Linux/macOS only!
```

Once you run the activation command above, you should see `(venv)` in your prompt, and you're ready to install and run the application!
