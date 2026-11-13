"""
GUI: Speed Control Tab

Interface for writing MDR speed settings to PLC.

Thread-Safe: Yes (PyQt6 signal-based)
Features:
- Numeric speed input (DINT)
- Write button with validation
- Current value display
- Read-back verification
- Status messages
"""

import logging
from typing import Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                              QSpinBox, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSlot

from plc.plc_manager import PLCManager

logger = logging.getLogger(__name__)


class SpeedControlTab(QWidget):
    """
    Speed control interface for MDR motors.
    
    Features:
    - DINT input field with range validation
    - Write speed to PLC
    - Current value read-back
    - Status messages
    - Communication error display
    """

    SPEED_TAG = "MDR_Speed_Setting"
    MIN_SPEED = 0
    MAX_SPEED = 5000

    def __init__(self, plc_manager: PLCManager):
        super().__init__()
        self.plc_manager = plc_manager
        self._init_ui()
        logger.debug("Initialized SpeedControlTab")

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Current value display
        current_layout = QHBoxLayout()
        current_layout.addWidget(QLabel("Current Speed Setting:"))
        self.current_value_label = QLabel("--")
        self.current_value_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        current_layout.addWidget(self.current_value_label)
        current_layout.addStretch()
        layout.addLayout(current_layout)

        # Speed input
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("New Speed Value (0-5000 (mm/s)):"))

        self.speed_input = QSpinBox()
        self.speed_input.setMinimum(self.MIN_SPEED)
        self.speed_input.setMaximum(self.MAX_SPEED)
        self.speed_input.setValue(50)
        self.speed_input.setMinimumWidth(100)

        input_layout.addWidget(self.speed_input)
        input_layout.addStretch()
        layout.addLayout(input_layout)

        # Action buttons
        button_layout = QHBoxLayout()

        self.read_btn = QPushButton("Read Current Value")
        self.read_btn.clicked.connect(self._on_read_value)

        self.write_btn = QPushButton("Write Speed")
        self.write_btn.setMinimumHeight(40)
        self.write_btn.setStyleSheet("background-color: #2196F3; color: white; font-weight: bold;")
        self.write_btn.clicked.connect(self._on_write_value)

        button_layout.addWidget(self.read_btn)
        button_layout.addWidget(self.write_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Status message
        layout.addWidget(QLabel("Status:"))
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("background-color: #f5f5f5; padding: 10px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

    def _on_read_value(self) -> None:
        """Read current speed from PLC."""
        if not self.plc_manager.is_connected():
            self._set_status("Error: PLC not connected", error=True)
            return

        try:
            value = self.plc_manager.read_tag(self.SPEED_TAG)
            if value is not None:
                self.current_value_label.setText(str(int(value)))
                self._set_status(f"Read {self.SPEED_TAG} = {int(value)}")
                logger.info(f"Read speed: {int(value)}")
            else:
                self._set_status("Failed to read speed", error=True)
        except Exception as e:
            error_msg = f"Error reading speed: {str(e)}"
            self._set_status(error_msg, error=True)
            logger.error(error_msg)

    def _on_write_value(self) -> None:
        """Write speed value to PLC."""
        if not self.plc_manager.is_connected():
            self._set_status("Error: PLC not connected", error=True)
            return

        speed_value = self.speed_input.value()

        try:
            success = self.plc_manager.write_tag(self.SPEED_TAG, speed_value, "DINT")

            if success:
                self._set_status(f"Wrote {self.SPEED_TAG} = {speed_value}")
                # Read back to verify
                self._verify_write(speed_value)
            else:
                self._set_status("Write failed", error=True)

        except Exception as e:
            error_msg = f"Error writing speed: {str(e)}"
            self._set_status(error_msg, error=True)
            logger.error(error_msg)

    def _verify_write(self, expected_value: int) -> None:
        """Verify written value by reading back."""
        try:
            actual_value = self.plc_manager.read_tag(self.SPEED_TAG)
            if actual_value is not None:
                actual_int = int(actual_value)
                if actual_int == expected_value:
                    self.current_value_label.setText(str(actual_int))
                    self._set_status(f"Write verified: {actual_int}")
                    logger.info(f"Write verified: {actual_int}")
                else:
                    error_msg = f"Verification failed: wrote {expected_value}, read {actual_int}"
                    self._set_status(error_msg, error=True)
                    logger.warning(error_msg)
        except Exception as e:
            logger.warning(f"Failed to verify write: {e}")

    def _set_status(self, message: str, error: bool = False) -> None:
        """Update status label."""
        if error:
            self.status_label.setStyleSheet("background-color: #ffcdd2; padding: 10px; color: red;")
        else:
            self.status_label.setStyleSheet("background-color: #c8e6c9; padding: 10px; color: green;")
        self.status_label.setText(message)
