# Development Guide

## Development Environment Setup

### Prerequisites
- Python 3.12+
- Git
- Virtual environment (recommended)
- IDE: VS Code or PyCharm

### Initial Setup

```bash
# Clone repository
git clone https://github.com/SamHGreco/PulseRoller-Datalogger.git
cd PulseRoller-Datalogger

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

# Install dependencies with dev tools
pip install -r requirements.txt
pip install pytest pytest-qt black flake8

# Run application
python mdr_logger.py
```

## Project Structure

```
PulseRoller-Datalogger/
├── mdr_logger.py                 # Entry point
├── requirements.txt              # Dependencies
├── README.md                     # User documentation
├── ARCHITECTURE.md               # System design
├── CONFIG.md                     # Configuration reference
├── DEVELOPMENT.md                # This file
├── example_motor_config.json     # Config example
├── core/
│   ├── __init__.py
│   └── motor_config.py           # Motor management
├── data/
│   ├── __init__.py
│   ├── trend_buffer.py           # Circular buffer
│   └── data_recorder.py          # Recording engine
├── plc/
│   ├── __init__.py
│   └── plc_manager.py            # PLC communication
└── gui/
    ├── __init__.py
    ├── main_window.py            # Main application
    ├── widgets.py                # Reusable components
    ├── live_trends_tab.py        # Graph display
    ├── motor_config_tab.py       # Motor management UI
    ├── recording_tab.py          # Recording UI
    ├── speed_control_tab.py      # Speed control UI
    └── diagnostics_tab.py        # System health UI
```

## Code Organization Principles

### 1. Separation of Concerns
- **Core modules** (core/): Business logic
- **PLC modules** (plc/): External communication
- **Data modules** (data/): Storage and buffers
- **GUI modules** (gui/): User interface only

### 2. Thread Safety
- All PLC operations in background threads
- PyQt6 signals for thread-safe communication
- RLock for shared mutable state
- No blocking UI operations

### 3. Testability
- Each module independent
- Dependency injection via constructors
- Mockable external dependencies (PLC)
- Clear interfaces

## Coding Standards

### Python Style
- **PEP 8**: Follow Python style guide
- **Type Hints**: Required for all functions
- **Docstrings**: Google style docstrings
- **Naming**: snake_case for functions/variables, PascalCase for classes

### Example Function
```python
def calculate_average_current(motor_id: str, start_time: datetime, 
                             end_time: datetime) -> Optional[float]:
    """
    Calculate average current for a motor in time range.
    
    Args:
        motor_id: Unique motor identifier
        start_time: Start of time range
        end_time: End of time range
        
    Returns:
        Average current in mA or None if no data
        
    Raises:
        ValueError: If time range is invalid
    """
```

### Comments
- Only comment complex logic
- Explain "why" not "what"
- Keep comments up-to-date with code

```python
# Good: Explains why
# Use multi-tag read instead of individual reads to reduce
# EtherNet/IP traffic by 80% with multiple motors
results = plc.read(tag1, tag2, tag3)

# Bad: Obvious from code
# Loop through tags
for tag in tags:
    plc.read(tag)
```

## Testing

### Unit Tests
```python
# tests/test_motor_config.py
import pytest
from core.motor_config import MotorConfigManager, Motor

def test_add_motor():
    manager = MotorConfigManager()
    motor_id = manager.add_motor("Test Motor", "Tag.Name")
    assert motor_id is not None
    assert manager.get_motor(motor_id).name == "Test Motor"

def test_motor_validation():
    manager = MotorConfigManager()
    with pytest.raises(ValueError):
        manager.add_motor("", "Tag")  # Empty name
    with pytest.raises(ValueError):
        manager.add_motor("Motor", "")  # Empty tag
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_motor_config.py

# Run with coverage
pytest --cov=. --cov-report=html

# Run with verbose output
pytest -v
```

## Debugging

### Logging
```python
import logging

logger = logging.getLogger(__name__)

# Set level in mdr_logger.py
logging.basicConfig(level=logging.DEBUG)

# In code
logger.debug(f"Detailed info: {variable}")
logger.info("Major operation completed")
logger.warning("Non-critical issue detected")
logger.error("Operation failed", exc_info=True)
```

### Viewing Logs
```bash
# Follow logs in real-time
tail -f ~/.mdr_logger/mdr_logger.log

# Last 50 lines
tail -50 ~/.mdr_logger/mdr_logger.log

# Search for errors
grep ERROR ~/.mdr_logger/mdr_logger.log
```

### PyQt6 Debugging
```python
# Add to main_window.py to debug signals
@pyqtSlot()
def _on_motor_changed(self):
    logger.debug(f"Motor changed signal received")
    logger.debug(f"Current motor list: {self.config_manager.get_all_motors()}")

# Debug thread issues
import threading
logger.debug(f"Current thread: {threading.current_thread().name}")
```

## Performance Profiling

### CPU Profiling
```python
import cProfile
import pstats
from io import StringIO

pr = cProfile.Profile()
pr.enable()

# ... code to profile ...

pr.disable()
s = StringIO()
ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
ps.print_stats()
print(s.getvalue())
```

### Memory Profiling
```bash
pip install memory-profiler

# Profile specific function
python -m memory_profiler mdr_logger.py

# Or decorate function
from memory_profiler import profile

@profile
def my_function():
    pass
```

## Common Development Tasks

### Adding a New Motor Field

1. **Update Motor dataclass** (core/motor_config.py)
   ```python
   @dataclass
   class Motor:
       name: str
       plc_tag: str
       enabled: bool = True
       motor_id: str = field(default_factory=lambda: "")
       # Add new field:
       status: str = "OK"
   ```

2. **Update validation** (core/motor_config.py)
   ```python
   @staticmethod
   def _validate_motor_data(name: str, plc_tag: str, status: str) -> None:
       # Add validation for new field
       if status not in ["OK", "ERROR"]:
           raise ValueError("Invalid status")
   ```

3. **Update GUI table** (gui/motor_config_tab.py)
   ```python
   class MotorTableModel:
       COLUMNS = ['Motor Name', 'PLC Tag', 'Status', 'Enabled']
       COL_STATUS = 2  # Add column index
   ```

4. **Update persistence** (core/motor_config.py)
   - Motor.to_dict() and from_dict() handle automatically

### Adding a New Tab

1. **Create new tab file** (gui/my_tab.py)
   ```python
   from PyQt6.QtWidgets import QWidget, QVBoxLayout
   
   class MyNewTab(QWidget):
       def __init__(self, plc_manager, ...):
           super().__init__()
           self._init_ui()
       
       def _init_ui(self):
           layout = QVBoxLayout(self)
           # Add widgets
   ```

2. **Import in main_window.py**
   ```python
   from gui.my_tab import MyNewTab
   ```

3. **Add to tabs in MainWindow._init_ui()**
   ```python
   self.my_tab = MyNewTab(self.plc_manager, self.trend_buffer, self.data_recorder)
   self.tabs.addTab(self.my_tab, "My Tab")
   ```

### Adding PLC Read

1. **Add read capability** (plc/plc_manager.py)
   ```python
   def read_custom_tag(self, tag_name: str) -> Optional[float]:
       return self.read_tag(tag_name)
   ```

2. **Use in tab**
   ```python
   def _on_read_clicked(self):
       value = self.plc_manager.read_custom_tag("TagName")
       if value is not None:
           self.value_label.setText(str(value))
   ```

### Adding PLC Write

1. **Add write capability** (plc/plc_manager.py)
   ```python
   def write_custom_tag(self, tag_name: str, value: int) -> bool:
       return self.write_tag(tag_name, value, "DINT")
   ```

2. **Add validation** (gui/speed_control_tab.py)
   ```python
   def _validate_value(self, value: int) -> bool:
       if value < MIN_VALUE or value > MAX_VALUE:
           raise ValueError(f"Value must be between {MIN_VALUE} and {MAX_VALUE}")
       return True
   ```

## Commit Guidelines

### Message Format
```
Short summary (50 chars max)

Detailed explanation if needed (wrap at 72 chars).
Explain what and why, not how.

Fixes: #123
Related-To: #456
```

### Examples
```
Add multi-tag read optimization to PLCManager

Previously, reading N motors required N EtherNet/IP requests.
Now uses pycomm3's multi-read to send all tags in a single
request, reducing network traffic by 80-90%.

Performance improvement: 250ms interval with 10 motors
improved from 1.2 Hz to 3.8 Hz achieved poll rate.

Fixes: #42
```

```
Fix race condition in TrendBuffer during rapid updates

Add RLock around _buffer access to prevent data corruption
when multiple threads update simultaneously. Includes
additional safety check in get_all_data().

Relates-To: #78
```

## Release Checklist

### Before Release
- [ ] All tests passing
- [ ] Code coverage >80%
- [ ] No linting errors (black, flake8)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated
- [ ] Version bumped in mdr_logger.py
- [ ] Tested with target PLC
- [ ] Performance benchmarks acceptable

### Release Steps
```bash
# Update version
# Update CHANGELOG.md
# Run full test suite
pytest --cov=.

# Format code
black .

# Commit
git commit -m "Release v1.1.0"
git tag -a v1.1.0 -m "Release version 1.1.0"
git push origin main --tags

# Create release on GitHub
# Upload to PyPI if applicable
```

## Troubleshooting Development Issues

### ImportError: No module named 'pyqtgraph'
```bash
pip install -r requirements.txt
```

### PLC Connection Timeout
- Verify PLC IP address
- Check network connectivity: `ping <plc_ip>`
- Verify firewall allows port 44818
- Check PLC is powered and online

### GUI Not Responding
- Check logs for blocking operations
- Ensure PLC operations are in background thread
- Profile with cProfile for slow functions
- Check for infinite loops or sleep() in main thread

### Data Not Displaying
- Verify motors are enabled in config tab
- Check PLC tags are correct
- Verify PLC is connected (green indicator)
- Check diagnostics tab for errors
- Increase poll interval temporarily to test

## Resources

- **PyQt6 Documentation**: https://www.riverbankcomputing.com/static/Docs/PyQt6/
- **pycomm3 Documentation**: https://docs.chargetrip.com/projects/pycomm3/
- **pyqtgraph Documentation**: https://www.pyqtgraph.org/
- **Python Type Hints**: https://docs.python.org/3/library/typing.html
- **PEP 8 Style Guide**: https://pep8.org/
