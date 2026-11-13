"""
GUI Module: Core Application Widget

Base classes and utilities for GUI components.

Thread-Safe: Yes (PyQt6 signals handle thread safety)
"""

import logging
from typing import Optional
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QLineEdit, QSpinBox, QComboBox, QMessageBox, QTableWidget,
                              QTableWidgetItem)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QFont

logger = logging.getLogger(__name__)


class StatusIndicator(QWidget):
    """Visual indicator for connection/status display."""

    def __init__(self, label_text: str = "Status"):
        super().__init__()
        layout = QHBoxLayout(self)

        self.label = QLabel(label_text)
        self.indicator = QLabel("●")
        self.indicator.setFont(QFont("Arial", 14))
        self.set_status(False)

        layout.addWidget(self.label)
        layout.addWidget(self.indicator)
        layout.addStretch()

    def set_status(self, connected: bool):
        """Set indicator status (green=connected, red=disconnected)."""
        if connected:
            self.indicator.setStyleSheet("color: green;")
            self.indicator.setText("● Connected")
        else:
            self.indicator.setStyleSheet("color: red;")
            self.indicator.setText("● Disconnected")


class IPAddressInput(QWidget):
    """IP address input widget with validation."""

    valueChanged = pyqtSignal(str)

    def __init__(self, label: str = "PLC IP Address:"):
        super().__init__()
        layout = QHBoxLayout(self)

        self.label = QLabel(label)
        self.input = QLineEdit()
        self.input.setPlaceholderText("192.168.1.100")
        self.input.textChanged.connect(self.valueChanged.emit)

        layout.addWidget(self.label)
        layout.addWidget(self.input)

    def get_value(self) -> str:
        """Get IP address value."""
        return self.input.text().strip()

    def set_value(self, value: str):
        """Set IP address value."""
        self.input.setText(value)

    def is_valid(self) -> bool:
        """Validate IP address format."""
        ip = self.get_value()
        if not ip:
            return False
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        try:
            return all(0 <= int(part) <= 255 for part in parts)
        except ValueError:
            return False


class MotorTableModel:
    """Helper class for motor table management."""

    COLUMNS = ['Motor Name', 'PLC Tag', 'Enabled']
    COL_NAME = 0
    COL_TAG = 1
    COL_ENABLED = 2

    @staticmethod
    def setup_table(table: QTableWidget):
        """Configure table widget for motor display."""
        table.setColumnCount(len(MotorTableModel.COLUMNS))
        table.setHorizontalHeaderLabels(MotorTableModel.COLUMNS)
        table.horizontalHeader().setStretchLastSection(True)
        table.setColumnWidth(0, 200)
        table.setColumnWidth(1, 300)
        table.setColumnWidth(2, 80)

    @staticmethod
    def add_row(table: QTableWidget, motor_id: str, name: str, plc_tag: str, enabled: bool):
        """Add a row to the motor table."""
        row = table.rowCount()
        table.insertRow(row)

        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.ItemDataRole.UserRole, motor_id)
        table.setItem(row, MotorTableModel.COL_NAME, name_item)

        tag_item = QTableWidgetItem(plc_tag)
        table.setItem(row, MotorTableModel.COL_TAG, tag_item)

        enabled_item = QTableWidgetItem()
        enabled_item.setCheckState(Qt.CheckState.Checked if enabled else Qt.CheckState.Unchecked)
        table.setItem(row, MotorTableModel.COL_ENABLED, enabled_item)

    @staticmethod
    def get_row_motor_id(table: QTableWidget, row: int) -> Optional[str]:
        """Get motor ID from table row."""
        item = table.item(row, MotorTableModel.COL_NAME)
        if item:
            return item.data(Qt.ItemDataRole.UserRole)
        return None

    @staticmethod
    def clear_table(table: QTableWidget):
        """Clear all rows from table."""
        table.setRowCount(0)
