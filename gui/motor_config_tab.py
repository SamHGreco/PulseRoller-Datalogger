"""
GUI: Motor Configuration Tab

Manage motor definitions, enable/disable, and dynamic add/remove operations.

Thread-Safe: Yes (PyQt6 signal-based)
Features:
- Add/Remove/Edit motors
- Enable/Disable motors
- Automatic configuration persistence
"""

import logging
from typing import Dict, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget,
                              QTableWidgetItem, QLineEdit, QDialog, QLabel, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot

from core.motor_config import MotorConfigManager
from gui.widgets import MotorTableModel

logger = logging.getLogger(__name__)


class MotorConfigTab(QWidget):
    """
    Motor configuration management interface.
    
    Allows users to:
    - View all configured motors
    - Add new motors
    - Remove motors
    - Edit motor names and tags
    - Enable/disable motors
    
    Changes are automatically saved to configuration file.
    """

    motors_changed = pyqtSignal()  # Emitted when motor configuration changes

    def __init__(self, config_manager: MotorConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self._init_ui()
        self._load_motors()
        logger.debug("Initialized MotorConfigTab")

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Button panel
        button_layout = QHBoxLayout()

        self.add_btn = QPushButton("Add Motor")
        self.add_btn.clicked.connect(self._on_add_motor)

        self.edit_btn = QPushButton("Edit Selected")
        self.edit_btn.clicked.connect(self._on_edit_motor)

        self.remove_btn = QPushButton("Remove Selected")
        self.remove_btn.clicked.connect(self._on_remove_motor)

        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._load_motors)

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.edit_btn)
        button_layout.addWidget(self.remove_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_btn)

        layout.addLayout(button_layout)

        # Motor table
        self.motor_table = QTableWidget()
        MotorTableModel.setup_table(self.motor_table)
        self.motor_table.itemChanged.connect(self._on_table_item_changed)

        layout.addWidget(self.motor_table)

    def _load_motors(self) -> None:
        """Load and display all motors."""
        MotorTableModel.clear_table(self.motor_table)

        for motor in self.config_manager.get_all_motors():
            MotorTableModel.add_row(
                self.motor_table,
                motor.motor_id,
                motor.name,
                motor.plc_tag,
                motor.enabled
            )

    def _on_add_motor(self) -> None:
        """Handle add motor button click."""
        dialog = MotorEditDialog(self, is_new=True)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, plc_tag = dialog.get_values()
            try:
                self.config_manager.add_motor(name, plc_tag)
                self._load_motors()
                self.motors_changed.emit()
                logger.info(f"Added motor: {name}")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def _on_edit_motor(self) -> None:
        """Handle edit motor button click."""
        current_row = self.motor_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a motor to edit")
            return

        motor_id = MotorTableModel.get_row_motor_id(self.motor_table, current_row)
        if not motor_id:
            return

        motor = self.config_manager.get_motor(motor_id)
        if not motor:
            return

        dialog = MotorEditDialog(self, is_new=False, initial_name=motor.name,
                                 initial_tag=motor.plc_tag)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            name, plc_tag = dialog.get_values()
            try:
                self.config_manager.update_motor(motor_id, name=name, plc_tag=plc_tag)
                self._load_motors()
                self.motors_changed.emit()
                logger.info(f"Updated motor: {motor_id}")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def _on_remove_motor(self) -> None:
        """Handle remove motor button click."""
        current_row = self.motor_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select a motor to remove")
            return

        motor_id = MotorTableModel.get_row_motor_id(self.motor_table, current_row)
        if not motor_id:
            return

        motor = self.config_manager.get_motor(motor_id)
        if not motor:
            return

        reply = QMessageBox.question(self, "Confirm",
                                     f"Remove motor '{motor.name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                self.config_manager.remove_motor(motor_id)
                self._load_motors()
                self.motors_changed.emit()
                logger.info(f"Removed motor: {motor_id}")
            except ValueError as e:
                QMessageBox.warning(self, "Error", str(e))

    def _on_table_item_changed(self, item: QTableWidgetItem) -> None:
        """Handle table cell edits."""
        row = item.row()
        motor_id = MotorTableModel.get_row_motor_id(self.motor_table, row)
        if not motor_id:
            return

        motor = self.config_manager.get_motor(motor_id)
        if not motor:
            return

        col = item.column()

        try:
            if col == MotorTableModel.COL_NAME:
                new_name = item.text()
                self.config_manager.update_motor(motor_id, name=new_name)
                self.motors_changed.emit()

            elif col == MotorTableModel.COL_TAG:
                new_tag = item.text()
                self.config_manager.update_motor(motor_id, plc_tag=new_tag)
                self.motors_changed.emit()

            elif col == MotorTableModel.COL_ENABLED:
                is_checked = item.checkState() == Qt.CheckState.Checked
                self.config_manager.update_motor(motor_id, enabled=is_checked)
                self.motors_changed.emit()

        except ValueError as e:
            logger.error(f"Error updating motor: {e}")
            QMessageBox.warning(self, "Error", str(e))
            self._load_motors()

    def get_enabled_motor_tags(self) -> Dict[str, str]:
        """Get mapping of enabled motor IDs to PLC tags."""
        motors = self.config_manager.get_enabled_motors()
        return {motor.motor_id: motor.plc_tag for motor in motors}


class MotorEditDialog(QDialog):
    """Dialog for editing motor properties."""

    def __init__(self, parent: QWidget, is_new: bool = True,
                 initial_name: str = "", initial_tag: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Motor Configuration" if is_new else "Edit Motor")
        self.setModal(True)
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # Motor name
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Motor Name:"))
        self.name_input = QLineEdit()
        self.name_input.setText(initial_name)
        self.name_input.setPlaceholderText("e.g., Left MDR - Line 1")
        name_layout.addWidget(self.name_input)
        layout.addLayout(name_layout)

        # PLC tag
        tag_layout = QHBoxLayout()
        tag_layout.addWidget(QLabel("PLC Tag:"))
        self.tag_input = QLineEdit()
        self.tag_input.setText(initial_tag)
        self.tag_input.setPlaceholderText("e.g., ConveylinxAi2_1AOI.I_Current_Left_MDR")
        tag_layout.addWidget(self.tag_input)
        layout.addLayout(tag_layout)

        # Buttons
        button_layout = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(ok_btn)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def get_values(self) -> tuple:
        """Get entered values."""
        return (self.name_input.text(), self.tag_input.text())
