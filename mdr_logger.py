"""
MDR Current Data Logger Application Entry Point

A professional desktop application for monitoring and recording Motor Driven Roller (MDR)
current data from Allen Bradley CompactLogix L18ER PLC using real-time trending and CSV export.

Architecture:
- Thread-safe PLC communication using pycomm3
- Real-time data visualization with pyqtgraph
- Circular buffers for memory-efficient data storage
- Independent recording engine for long-term data capture
- Multi-tag PLC reads for optimal performance

Author: Automation Engineering
License: Proprietary
"""

import sys
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication

# Ensure log directory exists before configuring logging
log_dir = Path.home() / '.mdr_logger'
log_dir.mkdir(parents=True, exist_ok=True)

# Configure root logger before importing modules
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / 'mdr_logger.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

from gui.main_window import MainWindow


def main():
    """Initialize and run the MDR Logger application."""
    logging.info("Starting MDR Current Data Logger Application")
    
    app = QApplication(sys.argv)
    app.setApplicationName("MDR Current Data Logger")
    app.setApplicationVersion("1.0.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
