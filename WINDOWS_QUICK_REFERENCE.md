# Windows Quick Reference Card

## 🚀 One-Command Quick Start (Copy & Paste)

Open PowerShell and paste this entire block:

```powershell
cd "C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python mdr_logger.py
```

**That's it!** The application will launch.

---

## ✅ Step-by-Step Quick Setup

### Step 1: Open PowerShell
- Press `Win + R`
- Type `powershell` and press Enter

### Step 2: Navigate to Project
```powershell
cd "C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger"
```

### Step 3: Create Virtual Environment (One-time only)
```powershell
python -m venv venv
```

### Step 4: Activate Virtual Environment
```powershell
venv\Scripts\activate
```

✅ You should see `(venv)` at the start of your command line

### Step 5: Install Dependencies (One-time only)
```powershell
pip install -r requirements.txt
```

### Step 6: Run Application
```powershell
python mdr_logger.py
```

The application window opens immediately.

---

## 📝 Important Windows Notes

### Virtual Environment Activation
The correct Windows command is:
```powershell
venv\Scripts\activate
```

**NOT:**
```powershell
source venv/bin/activate    # ❌ This is for Linux/macOS!
```

### After Restart
If you close PowerShell, just:
1. Open PowerShell again
2. Run: `cd "C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger"`
3. Run: `venv\Scripts\activate`
4. Run: `python mdr_logger.py`

### Deactivate Virtual Environment
When done, type:
```powershell
deactivate
```

---

## 🔄 Subsequent Runs

After the first setup, you only need:

```powershell
cd "C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger"
venv\Scripts\activate
python mdr_logger.py
```

---

## ❓ Troubleshooting

| Problem | Solution |
|---------|----------|
| `python: not found` | Install Python from python.org or use `py` instead |
| `venv\Scripts\activate` doesn't work | Make sure you're in the project directory first |
| `pip install` fails | Make sure venv is activated (see `(venv)` in prompt) |
| Application won't start | Check the log: `type $env:USERPROFILE\.mdr_logger\mdr_logger.log` |

---

## 💾 File Locations (Windows)

| What | Where |
|------|-------|
| Project | `C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger` |
| Config | `C:\Users\sam04261\.mdr_logger\motor_config.json` |
| Logs | `C:\Users\sam04261\.mdr_logger\mdr_logger.log` |
| Virtual Env | `C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger\venv` |

---

## 🎯 Typical Workflow

```powershell
# Day 1: Initial Setup (do once)
cd "C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger"
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python mdr_logger.py

# Day 2+: Just run these 3 commands
cd "C:\Users\sam04261\OneDrive - Laitram\Documents\GitHub\PulseRoller-Datalogger"
venv\Scripts\activate
python mdr_logger.py
```

---

## 🎓 Why Virtual Environment?

Virtual environments keep your project's dependencies isolated:
- Different projects can use different versions of packages
- Doesn't affect your system Python installation
- Easy to clean up (just delete the `venv` folder)

Think of it as a "sandbox" for this project.

---

## 📞 Need Help?

1. **Check** [WINDOWS_SETUP.md](WINDOWS_SETUP.md) for detailed troubleshooting
2. **Read** [QUICKSTART.md](QUICKSTART.md) for first use
3. **See** [README.md](README.md) for complete documentation
4. **Review** logs: `$env:USERPROFILE\.mdr_logger\mdr_logger.log`

---

## ⌨️ PowerShell Tips

| Command | What It Does |
|---------|--------------|
| `dir` | List files in current folder |
| `cd foldername` | Go into a folder |
| `cd ..` | Go up one level |
| `pwd` | Show current folder path |
| `Clear-Host` | Clear screen |
| `exit` | Close PowerShell |

---

**You're ready!** Paste that first block into PowerShell and you're running. 🚀
