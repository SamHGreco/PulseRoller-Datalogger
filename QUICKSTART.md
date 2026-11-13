# Quick Start Guide

Get the MDR Current Data Logger running in 5 minutes.

## Installation (2 minutes)

### 1. Install Python 3.12
Download from https://www.python.org/downloads/

Verify installation:
```bash
python --version
# Output: Python 3.12.x
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- PyQt6 (GUI framework)
- pycomm3 (PLC communication)
- pyqtgraph (Real-time plotting)
- pandas (Data processing)
- numpy (Numerical computing)

## First Run (1 minute)

```bash
python mdr_logger.py
```

You should see:
1. Application window opens
2. Motor Configuration tab shows 4 default motors
3. All controls are ready
4. Status indicator shows "Disconnected"

## Connecting to Your PLC (1 minute)

1. **Enter PLC IP Address**
   - Top field: `192.168.1.100` (replace with your PLC IP)

2. **Click Connect**
   - Status indicator changes to green
   - Console shows "Connected to PLC"

3. **Verify Connection**
   - Go to **Diagnostics** tab
   - Check "PLC Connection Status"
   - Watch "Total Samples Collected" increase

## Viewing Live Data (1 minute)

1. **Go to Live Trends tab**
   - You should see real-time graphs updating
   - Multiple colored lines = different motors

2. **Explore Features**
   - Scroll mouse wheel to zoom
   - Click and drag to pan
   - Toggle motor visibility with checkboxes
   - Switch between "Single Graph" and "Individual Graphs" layout

## Recording a Session

1. **Go to Recording tab**

2. **Click Start Recording**
   - Status shows "Recording"
   - Timer shows elapsed time
   - Sample count increases

3. **Let it run for 30 seconds**

4. **Click Stop Recording**
   - Status shows "Stopped"
   - Sample count frozen

5. **Click Export to CSV**
   - Choose save location
   - Opens CSV file with timestamp and current values

## Configuring Your Motors

If the default 4 motors don't match your setup:

1. **Go to Motor Configuration tab**

2. **Edit Existing Motor**
   - Click row to select
   - Click "Edit Selected"
   - Change name and PLC tag
   - Click OK

3. **Add New Motor**
   - Click "Add Motor"
   - Enter motor name (e.g., "Motor 5 - Center")
   - Enter PLC tag (e.g., `ConveylinxAi2_3AOI.I_Current_Center_MDR`)
   - Click OK

4. **Remove Motor**
   - Click row to select
   - Click "Remove Selected"
   - Confirm deletion

5. **Configuration is automatically saved**

## Speed Control

To write speed settings to the PLC:

1. **Go to Speed Control tab**

2. **Click Read Current Value**
   - Shows current MDR_Speed_Setting value

3. **Enter New Speed (0-100)**

4. **Click Write Speed**
   - Application verifies the write
   - Shows success or error message

## Understanding the Interface

### Tabs

| Tab | Purpose |
|-----|---------|
| **Motor Configuration** | Add/edit/remove motors, change PLC tags |
| **Live Trends** | Real-time graphs of motor currents |
| **Recording** | Start/stop recording, export to CSV |
| **Speed Control** | Write speed values to PLC |
| **Diagnostics** | System health, performance metrics |

### Key Indicators

| Indicator | Meaning |
|-----------|---------|
| **Green ●** | PLC connected |
| **Red ●** | PLC disconnected |
| **Poll Rate: X Hz** | Samples per second achieved |
| **Recording** | Data is being saved |
| **Graph Buffer** | Size of display buffer (diagnostics) |

### Control Panel

```
┌─────────────────────────────────────────┐
│ PLC IP: [192.168.1.100] [Connect] [Disconnect] │
│ Polling Interval: [250] ms              │
│ ● Connected    Poll Rate: 4.23 Hz       │
└─────────────────────────────────────────┘
```

## Troubleshooting

### "Cannot connect to PLC"
- Verify PLC IP address
- Ping the PLC: `ping 192.168.1.100`
- Check firewall settings
- Verify PLC is powered on

### "No data in graphs"
- Check PLC is connected (green indicator)
- Verify motors are enabled (Motor Configuration tab)
- Check PLC tag names match your configuration
- Go to Diagnostics tab and check "Total Samples Collected"

### "CSV is empty"
- Make sure recording was stopped before export
- Check "Recorded Samples" in Recording tab
- Try recording for at least 1 second

### Application slow or unresponsive
- Reduce polling interval (set higher ms value)
- Disable motors you're not using
- Close other programs
- Check Diagnostics for errors

## Configuration Files

Application data is stored in your home directory:

```
~/.mdr_logger/
├── motor_config.json     # Motor definitions
└── mdr_logger.log        # Application log
```

To reset to default configuration:
```bash
rm ~/.mdr_logger/motor_config.json
# Restart application
```

## Performance Tips

1. **For faster polling (more Hz)**
   - Use multi-tag reads (already enabled)
   - Reduce number of motors to essential ones
   - Increase polling interval (ms) value

2. **For longer recording sessions**
   - Reduce graph time range (Live Trends)
   - Disable unused motors
   - Increase polling interval

3. **For best network performance**
   - Keep PLC on same network segment
   - Minimize other EtherNet/IP traffic
   - Use 1 Gbps network connection

## Next Steps

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Understand system design
- **[CONFIG.md](CONFIG.md)** - Detailed configuration reference
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development guidelines
- **[README.md](README.md)** - Complete documentation

## Getting Help

### Check These First
1. **Diagnostics Tab** - See errors and metrics
2. **Application Logs** - `~/.mdr_logger/mdr_logger.log`
3. **README.md** - Troubleshooting section
4. **Console Output** - Run from terminal to see debug info

### Enable Debug Logging
Edit `mdr_logger.py` line 13:
```python
logging.basicConfig(level=logging.DEBUG)  # More detailed output
```

## Common Tasks

### Change Default PLC IP
Edit `gui/main_window.py` - `_create_connection_panel()` method

### Add More Default Motors
Edit `core/motor_config.py` - `MotorConfigManager.DEFAULT_MOTORS` list

### Change Graph Time Range Options
Edit `gui/live_trends_tab.py` - `time_range_combo` initialization

### Adjust Polling Interval Range
Edit `gui/main_window.py` - `poll_interval_spin` minimum/maximum values

## Summary

You now have:
✅ Application running
✅ Connected to PLC
✅ Live data streaming
✅ Recording capability
✅ CSV export working
✅ Full documentation

**Next**: Configure motors specific to your setup, then start monitoring!
