"""
GUI: Main Application Window

Orchestrates all tabs and manages application state.
Coordinates PLC communication, data recording, and visualization.

Thread-Safe: Yes (PyQt6 signals for inter-thread communication)
"""

import logging
import threading
import time
from datetime import datetime

from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
                              QLabel, QPushButton, QMessageBox, QSpinBox)
from PyQt6.QtCore import Qt, pyqtSignal, pyqtSlot, QTimer

from core.motor_config import MotorConfigManager
from data.trend_buffer import TrendBuffer
from data.data_recorder import DataRecorder
from plc.plc_manager import PLCManager
from gui.widgets import IPAddressInput, StatusIndicator
from gui.motor_config_tab import MotorConfigTab
from gui.live_trends_tab import LiveTrendsTab
from gui.recording_tab import RecordingControlTab
from gui.speed_control_tab import SpeedControlTab
from gui.diagnostics_tab import DiagnosticsTab

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window.
    
    Architecture:
    - PLCManager: Background thread for PLC communication
    - MotorConfigManager: Motor definition persistence
    - TrendBuffer: Circular buffer for graph display
    - DataRecorder: Independent long-term recording
    - Multiple tabs for different functions
    
    Data Flow:
    1. PLCManager reads enabled motor tags (multi-tag read for efficiency)
    2. Data emitted via DataUpdated signal
    3. TrendBuffer and DataRecorder both receive samples
    4. LiveTrendsTab displays TrendBuffer data
    5. RecordingControlTab manages DataRecorder
    """

    data_acquired = pyqtSignal(dict)  # {motor_id: current_mA}

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MDR Current Data Logger")
        self.setGeometry(100, 100, 1400, 900)

        # Initialize core components
        self.config_manager = MotorConfigManager()
        self.trend_buffer = TrendBuffer(max_samples=8000)
        self.data_recorder = DataRecorder()
        self.plc_manager = PLCManager()

        # Connect signals
        self.plc_manager.DataUpdated.connect(self._on_plc_data_updated)
        self.plc_manager.Connected.connect(self._on_plc_connected)
        self.plc_manager.Disconnected.connect(self._on_plc_disconnected)
        self.plc_manager.ErrorOccurred.connect(self._on_plc_error)

        self.data_acquired.connect(self._on_data_acquired)

        # Build UI
        self._init_ui()

        # Initialize motor list
        self._update_motor_list()

        # Start polling thread for PLC reading
        self.polling_thread = None
        self.polling_running = False

        logger.info("Initialized MainWindow")

    def _init_ui(self):
        """Initialize the main user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Connection panel
        connection_panel = self._create_connection_panel()
        layout.addLayout(connection_panel)

        # Sampling settings
        sampling_panel = self._create_sampling_panel()
        layout.addLayout(sampling_panel)

        # Status bar
        status_layout = QHBoxLayout()
        self.status_indicator = StatusIndicator("PLC Status:")
        self.actual_poll_rate_label = QLabel("Poll Rate: -- Hz")
        self.actual_poll_rate_label.setStyleSheet("font-weight: bold;")
        status_layout.addWidget(self.status_indicator)
        status_layout.addStretch()
        status_layout.addWidget(self.actual_poll_rate_label)
        layout.addLayout(status_layout)

        # Tabs
        self.tabs = QTabWidget()

        self.config_tab = MotorConfigTab(self.config_manager)
        self.config_tab.motors_changed.connect(self._on_motors_changed)

        self.trends_tab = LiveTrendsTab(self.trend_buffer)

        self.recording_tab = RecordingControlTab(self.data_recorder)
        self.recording_tab.recording_started.connect(self._on_recording_started)
        self.recording_tab.recording_stopped.connect(self._on_recording_stopped)

        self.speed_tab = SpeedControlTab(self.plc_manager)

        self.diagnostics_tab = DiagnosticsTab(self.plc_manager, self.trend_buffer,
                                              self.data_recorder)

        self.tabs.addTab(self.config_tab, "Motor Configuration")
        self.tabs.addTab(self.trends_tab, "Live Trends")
        self.tabs.addTab(self.recording_tab, "Recording")
        self.tabs.addTab(self.speed_tab, "Speed Control")
        self.tabs.addTab(self.diagnostics_tab, "Diagnostics")

        layout.addWidget(self.tabs)

        # Timer for periodic updates
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._periodic_update)
        self.update_timer.start(1000)  # Update every 1 second

    def _create_connection_panel(self) -> QHBoxLayout:
        """Create PLC connection control panel."""
        layout = QHBoxLayout()

        self.ip_input = IPAddressInput("PLC IP Address:")
        layout.addWidget(self.ip_input)

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setMinimumWidth(100)
        self.connect_btn.clicked.connect(self._on_connect_clicked)
        layout.addWidget(self.connect_btn)

        self.disconnect_btn = QPushButton("Disconnect")
        self.disconnect_btn.setMinimumWidth(100)
        self.disconnect_btn.setEnabled(False)
        self.disconnect_btn.clicked.connect(self._on_disconnect_clicked)
        layout.addWidget(self.disconnect_btn)

        return layout

    def _create_sampling_panel(self) -> QHBoxLayout:
        """Create sampling configuration panel."""
        layout = QHBoxLayout()

        layout.addWidget(QLabel("Polling Interval (ms):"))

        self.poll_interval_spin = QSpinBox()
        self.poll_interval_spin.setMinimum(50)
        self.poll_interval_spin.setMaximum(10000)
        self.poll_interval_spin.setValue(250)
        self.poll_interval_spin.setSingleStep(50)
        self.poll_interval_spin.setMinimumWidth(100)
        self.poll_interval_spin.valueChanged.connect(self._on_poll_interval_changed)

        layout.addWidget(self.poll_interval_spin)
        layout.addStretch()

        return layout

    @pyqtSlot()
    def _on_connect_clicked(self) -> None:
        """Handle connect button click."""
        if not self.ip_input.is_valid():
            QMessageBox.warning(self, "Invalid IP", "Please enter a valid IP address")
            return

        plc_ip = self.ip_input.get_value()

        if self.plc_manager.connect(plc_ip):
            self.connect_btn.setEnabled(False)
            self.disconnect_btn.setEnabled(True)
            self.ip_input.input.setEnabled(False)
            logger.info(f"Connected to PLC at {plc_ip}")
        else:
            QMessageBox.critical(self, "Connection Failed",
                               "Failed to connect to PLC. Check IP address and PLC status.")

    @pyqtSlot()
    def _on_disconnect_clicked(self) -> None:
        """Handle disconnect button click."""
        self.plc_manager.disconnect()

    def _on_plc_connected(self) -> None:
        """Handle PLC connection established."""
        self.status_indicator.set_status(True)
        self._start_polling()
        logger.info("PLC connected")

    def _on_plc_disconnected(self) -> None:
        """Handle PLC disconnection."""
        self._stop_polling()
        self.status_indicator.set_status(False)
        self.connect_btn.setEnabled(True)
        self.disconnect_btn.setEnabled(False)
        self.ip_input.input.setEnabled(True)
        logger.info("PLC disconnected")

    def _on_plc_error(self, error_msg: str) -> None:
        """Handle PLC error."""
        logger.error(f"PLC Error: {error_msg}")

    @pyqtSlot(dict)
    def _on_plc_data_updated(self, motor_values: dict) -> None:
        """Handle PLC data update from background thread."""
        self.data_acquired.emit(motor_values)

    @pyqtSlot(dict)
    def _on_data_acquired(self, motor_values: dict) -> None:
        """
        Process acquired motor data.
        
        Distributes data to:
        1. TrendBuffer (for graph display)
        2. DataRecorder (if recording)
        """
        timestamp = datetime.now()

        # Store in trend buffer for graph display
        self.trend_buffer.add_sample(motor_values, timestamp)

        # Store in recorder if recording
        if self.data_recorder.is_recording():
            self.data_recorder.add_sample(motor_values, timestamp)

    def _on_poll_interval_changed(self, value: int) -> None:
        """Handle polling interval change."""
        self.plc_manager.set_poll_interval(value)
        logger.info(f"Set polling interval to {value}ms")

    def _on_motors_changed(self) -> None:
        """Handle motor configuration change."""
        self._update_motor_list()
        if self.plc_manager.is_connected():
            # Restart polling with new motor list
            self._stop_polling()
            self._start_polling()

    def _on_recording_started(self) -> None:
        """Handle recording start."""
        logger.info("Recording started")

    def _on_recording_stopped(self) -> None:
        """Handle recording stop."""
        logger.info("Recording stopped")

    def _update_motor_list(self) -> None:
        """Update motor configuration in all components."""
        motors = self.config_manager.get_enabled_motors()
        motor_ids = [m.motor_id for m in motors]
        motor_names = self.config_manager.get_motor_names()

        # Update trends tab
        self.trends_tab.update_motor_list(motor_ids, motor_names)

        # Update recording tab
        self.recording_tab.set_motor_names(motor_names)

        logger.debug(f"Updated motor list: {len(motor_ids)} enabled motors")

    def _start_polling(self) -> None:
        """Start background polling thread."""
        if self.polling_running:
            logger.warning("Polling already running")
            return

        self.polling_running = True
        self.polling_thread = threading.Thread(target=self._polling_worker, daemon=True)
        self.polling_thread.start()
        logger.info("Started polling thread")

    def _stop_polling(self) -> None:
        """Stop background polling thread."""
        self.polling_running = False
        if self.polling_thread:
            self.polling_thread.join(timeout=2.0)
        logger.info("Stopped polling thread")

    def _polling_worker(self) -> None:
        """
        Background worker thread for PLC polling.
        
        Reads all enabled motor tags using multi-tag read for efficiency.
        Emits DataUpdated signal for each successful read.
        """
        logger.info("Polling worker started")

        while self.polling_running and self.plc_manager.is_connected():
            try:
                # Get list of enabled motors and their tags
                motors = self.config_manager.get_enabled_motors()
                if not motors:
                    time.sleep(0.1)
                    continue

                # Build motor_tags list for multi-tag read
                motor_tags = [(m.motor_id, m.plc_tag) for m in motors]

                # Perform multi-tag read (critical optimization!)
                motor_values = self.plc_manager.read_motor_tags(motor_tags)

                if motor_values is not None:
                    self.plc_manager.DataUpdated.emit(motor_values)

                # Sleep for configured polling interval
                time.sleep(self.plc_manager.poll_interval_s)

            except Exception as e:
                logger.error(f"Error in polling worker: {e}")
                time.sleep(0.5)

        logger.info("Polling worker stopped")

    @pyqtSlot()
    def _periodic_update(self) -> None:
        """Periodic UI update (every 1 second)."""
        # Update graph display
        self.trends_tab.update_plots()

        # Update recording tab display
        self.recording_tab._update_status()

        # Update actual poll rate display
        health = self.plc_manager.get_health_metrics()
        poll_rate = health.get('achieved_poll_rate', 0.0)
        self.actual_poll_rate_label.setText(f"Poll Rate: {poll_rate:.2f} Hz")

    def closeEvent(self, event):
        """Clean up on application close."""
        logger.info("Closing application")
        self._stop_polling()
        if self.plc_manager.is_connected():
            self.plc_manager.disconnect()
        event.accept()
