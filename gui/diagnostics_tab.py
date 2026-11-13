"""
GUI: Diagnostics Tab

System health and status monitoring display.

Thread-Safe: Yes (PyQt6 signal-based)
Features:
- PLC connection status
- Communication metrics
- Data collection statistics
- Graph performance metrics
- Recording state
"""

import logging
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
                              QTableWidgetItem)
from PyQt6.QtCore import Qt, QTimer

from plc.plc_manager import PLCManager
from data.trend_buffer import TrendBuffer
from data.data_recorder import DataRecorder

logger = logging.getLogger(__name__)


class DiagnosticsTab(QWidget):
    """
    System diagnostics and health monitoring.
    
    Displays:
    - PLC connection status
    - Communication metrics
    - Sample collection statistics
    - Polling rate information
    - Recording state
    - Memory usage
    """

    def __init__(self, plc_manager: PLCManager, trend_buffer: TrendBuffer,
                 data_recorder: DataRecorder):
        super().__init__()
        self.plc_manager = plc_manager
        self.trend_buffer = trend_buffer
        self.data_recorder = data_recorder

        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_diagnostics)
        self.update_timer.start(1000)  # Update every 1 second

        self._init_ui()
        logger.debug("Initialized DiagnosticsTab")

    def _init_ui(self):
        """Initialize the user interface."""
        layout = QVBoxLayout(self)

        # Diagnostics table
        self.diag_table = QTableWidget()
        self.diag_table.setColumnCount(2)
        self.diag_table.setHorizontalHeaderLabels(['Metric', 'Value'])
        self.diag_table.horizontalHeader().setStretchLastSection(True)
        self.diag_table.setColumnWidth(0, 250)

        layout.addWidget(QLabel("System Diagnostics:"))
        layout.addWidget(self.diag_table)

        # Initialize table rows
        self._init_table_rows()

    def _init_table_rows(self):
        """Initialize table rows for diagnostics."""
        metrics = [
            "PLC Connection Status",
            "PLC IP Address",
            "Total Samples Collected",
            "Samples Failed",
            "Success Rate (%)",
            "Configured Poll Interval (ms)",
            "Achieved Poll Rate (Hz)",
            "Graph Buffer Capacity (%)",
            "Graph Samples in Buffer",
            "Recording Status",
            "Recorded Samples",
            "Recording Duration",
            "Last Communication Error",
        ]

        self.diag_table.setRowCount(len(metrics))

        for i, metric in enumerate(metrics):
            name_item = QTableWidgetItem(metric)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.diag_table.setItem(i, 0, name_item)

            value_item = QTableWidgetItem("--")
            value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.diag_table.setItem(i, 1, value_item)

    def _update_diagnostics(self) -> None:
        """Update diagnostics display."""
        try:
            # Get PLC health metrics
            plc_metrics = self.plc_manager.get_health_metrics()

            # Get graph buffer stats
            graph_capacity = self.trend_buffer.get_capacity_percentage()
            graph_samples = self.trend_buffer.get_size()

            # Get recording stats
            is_recording = self.data_recorder.is_recording()
            recorded_samples = self.data_recorder.get_record_count()
            recording_duration = self.data_recorder.get_duration()

            # Update table
            updates = [
                ("PLC Connection Status", "Connected" if plc_metrics['connected'] else "Disconnected"),
                ("PLC IP Address", plc_metrics['plc_ip'] or "Not configured"),
                ("Total Samples Collected", str(plc_metrics['samples_read'])),
                ("Samples Failed", str(plc_metrics['samples_failed'])),
                ("Success Rate (%)", f"{plc_metrics['success_rate']:.1f}"),
                ("Configured Poll Interval (ms)", str(plc_metrics['configured_poll_interval_ms'])),
                ("Achieved Poll Rate (Hz)", f"{plc_metrics['achieved_poll_rate']:.2f}"),
                ("Graph Buffer Capacity (%)", f"{graph_capacity:.1f}"),
                ("Graph Samples in Buffer", str(graph_samples)),
                ("Recording Status", "Recording" if is_recording else "Stopped"),
                ("Recorded Samples", str(recorded_samples)),
                ("Recording Duration", self._format_duration(recording_duration)),
                ("Last Communication Error", plc_metrics['last_error']),
            ]

            for i, (metric, value) in enumerate(updates):
                self.diag_table.item(i, 1).setText(str(value))

        except Exception as e:
            logger.warning(f"Error updating diagnostics: {e}")

    @staticmethod
    def _format_duration(seconds: float) -> str:
        """Format duration in seconds as HH:MM:SS."""
        if seconds is None:
            return "N/A"
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def closeEvent(self, event):
        """Clean up on close."""
        self.update_timer.stop()
        super().closeEvent(event)
