"""
GUI: Recording Control Tab

Manage data recording sessions with start/stop controls and status display.

Thread-Safe: Yes (PyQt6 signal-based)
Features:
- Start/Stop recording
- Recording status indicator
- Recording duration timer
- CSV export dialog
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
                              QFileDialog, QMessageBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer

from data.data_recorder import DataRecorder
from gui.widgets import StatusIndicator

logger = logging.getLogger(__name__)


class RecordingControlTab(QWidget):
    """
    Recording control and management interface.
    
    Features:
    - Start/Stop recording buttons
    - Recording status display
    - Recording timer
    - Record count display
    - CSV export with file dialog
    """

    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal()

    def __init__(self, data_recorder: DataRecorder):
        super().__init__()
        self.data_recorder = data_recorder
        self.last_motor_names = {}
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_status)

        self._init_ui()
        logger.debug("Initialized RecordingControlTab")

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Status panel
        status_layout = QHBoxLayout()
        self.status_indicator = StatusIndicator("Recording Status:")
        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Timer display
        timer_layout = QHBoxLayout()
        timer_layout.addWidget(QLabel("Recording Duration:"))
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(self.timer_label.font())
        self.timer_label.setStyleSheet("font-weight: bold;")
        timer_layout.addWidget(self.timer_label)
        timer_layout.addStretch()
        layout.addLayout(timer_layout)

        # Record count
        count_layout = QHBoxLayout()
        count_layout.addWidget(QLabel("Samples Recorded:"))
        self.count_label = QLabel("0")
        self.count_label.setStyleSheet("font-weight: bold;")
        count_layout.addWidget(self.count_label)
        count_layout.addStretch()
        layout.addLayout(count_layout)

        # Control buttons
        button_layout = QHBoxLayout()

        self.start_btn = QPushButton("Start Recording")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        self.start_btn.clicked.connect(self._on_start_recording)

        self.stop_btn = QPushButton("Stop Recording")
        self.stop_btn.setMinimumHeight(40)
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold;")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop_recording)

        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.setMinimumHeight(40)
        self.export_btn.clicked.connect(self._on_export_csv)

        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(self.stop_btn)
        button_layout.addWidget(self.export_btn)

        layout.addLayout(button_layout)
        layout.addStretch()

    def set_motor_names(self, motor_names: dict):
        """Store motor names for CSV export."""
        self.last_motor_names = motor_names

    def _on_start_recording(self) -> None:
        """Handle start recording button click."""
        try:
            self.data_recorder.start_recording()
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.update_timer.start(100)  # Update display every 100ms
            self.status_indicator.set_status(True)
            self.recording_started.emit()
            logger.info("Recording started")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start recording: {str(e)}")
            logger.error(f"Failed to start recording: {e}")

    def _on_stop_recording(self) -> None:
        """Handle stop recording button click."""
        try:
            self.data_recorder.stop_recording()
            self.update_timer.stop()
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.status_indicator.set_status(False)
            self.recording_stopped.emit()
            logger.info("Recording stopped")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to stop recording: {str(e)}")
            logger.error(f"Failed to stop recording: {e}")

    def _on_export_csv(self) -> None:
        """Handle CSV export button click."""
        record_count = self.data_recorder.get_record_count()

        if record_count == 0:
            QMessageBox.warning(self, "No Data", "No recorded data to export")
            return

        # Open save file dialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Recording as CSV",
            str(Path.home() / f"mdr_recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"),
            "CSV Files (*.csv)"
        )

        if not file_path:
            return

        try:
            self.data_recorder.export_to_csv(Path(file_path), self.last_motor_names)
            QMessageBox.information(self, "Success",
                                   f"Exported {record_count} samples to:\n{file_path}")
            logger.info(f"Exported CSV to {file_path}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export CSV: {str(e)}")
            logger.error(f"Failed to export CSV: {e}")

    def _update_status(self) -> None:
        """Update recording status display."""
        is_recording = self.data_recorder.is_recording()
        record_count = self.data_recorder.get_record_count()
        duration = self.data_recorder.get_duration()

        self.count_label.setText(str(record_count))

        if duration is not None:
            total_seconds = int(duration)
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.timer_label.setText(time_str)
