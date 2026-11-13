"""
GUI: Live Trends Tab

Real-time plotting of motor current data using pyqtgraph.
Supports multiple viewing modes, time ranges, and motor selection.

Thread-Safe: Yes (PyQt6 signal-based updates)
Features:
- Real-time updating graphs
- Configurable visible time range
- Multi-motor legend
- Mouse zoom and pan
- Single/multiple graph layouts
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                              QComboBox, QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt, pyqtSlot
import pyqtgraph as pg
import numpy as np

from data.trend_buffer import TrendBuffer

logger = logging.getLogger(__name__)

# Color palette for motors
MOTOR_COLORS = [
    (255, 0, 0),      # Red
    (0, 0, 255),      # Blue
    (0, 128, 0),      # Green
    (255, 165, 0),    # Orange
    (128, 0, 128),    # Purple
    (0, 128, 128),    # Teal
    (255, 192, 203),  # Pink
    (165, 42, 42),    # Brown
    (128, 128, 0),    # Olive
    (0, 0, 128),      # Navy
]


class LiveTrendsTab(QWidget):
    """
    Live trends visualization tab.
    
    Features:
    - Real-time data updates from TrendBuffer
    - Configurable time ranges (30s to 10 min)
    - Layout modes (single graph or individual graphs)
    - Motor visibility toggling
    - Mouse zoom/pan enabled
    """

    def __init__(self, trend_buffer: TrendBuffer):
        super().__init__()
        self.trend_buffer = trend_buffer
        self.motor_colors = {}
        self.plot_curves = {}  # {motor_id: PlotCurveItem}
        self.plot_items = {}   # {motor_id: PlotItem} for individual layout mode
        self.visible_motors = set()
        self.layout_mode = "single"  # "single" or "individual"

        self._init_ui()
        logger.debug("Initialized LiveTrendsTab")

    def _init_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)

        # Control panel
        control_layout = QHBoxLayout()

        self.time_range_combo = QComboBox()
        self.time_range_combo.addItems(["30 sec", "1 min", "2 min", "5 min", "10 min"])
        self.time_range_combo.setCurrentText("2 min")
        self.time_range_combo.currentTextChanged.connect(self._on_time_range_changed)

        self.layout_combo = QComboBox()
        self.layout_combo.addItems(["Single Graph", "Individual Graphs"])
        self.layout_combo.currentTextChanged.connect(self._on_layout_changed)

        control_layout.addWidget(QLabel("Time Range:"))
        control_layout.addWidget(self.time_range_combo)
        control_layout.addWidget(QLabel("Layout:"))
        control_layout.addWidget(self.layout_combo)
        control_layout.addStretch()

        layout.addLayout(control_layout)

        # Graph area
        self.graph_scroll = QScrollArea()
        self.graph_scroll.setWidgetResizable(True)
        self.graph_container = QWidget()
        self.graph_layout = QVBoxLayout(self.graph_container)
        self.graph_scroll.setWidget(self.graph_container)

        layout.addWidget(self.graph_scroll)

        # Motor visibility checkboxes
        visibility_layout = QHBoxLayout()
        visibility_layout.addWidget(QLabel("Visible Motors:"))
        self.motor_checkboxes = {}
        visibility_layout.addStretch()

        self.visibility_panel = QWidget()
        self.visibility_panel.setLayout(visibility_layout)
        layout.addWidget(self.visibility_panel)

    def update_motor_list(self, motor_ids: List[str], motor_names: Dict[str, str]) -> None:
        """
        Update the list of motors to display.
        
        Args:
            motor_ids: List of enabled motor IDs
            motor_names: Mapping of motor_id to display name
        """
        # Assign colors to motors
        for i, motor_id in enumerate(motor_ids):
            self.motor_colors[motor_id] = MOTOR_COLORS[i % len(MOTOR_COLORS)]
            self.visible_motors.add(motor_id)

        # Update visibility checkboxes
        for checkbox in self.motor_checkboxes.values():
            checkbox.deleteLater()
        self.motor_checkboxes.clear()

        visibility_layout = self.visibility_panel.layout()
        while visibility_layout.count() > 1:
            item = visibility_layout.takeAt(1)
            if item and item.widget():
                item.widget().deleteLater()

        for motor_id in motor_ids:
            checkbox = QCheckBox(motor_names.get(motor_id, motor_id))
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(lambda state, mid=motor_id: self._on_motor_visibility_changed(mid))
            self.motor_checkboxes[motor_id] = checkbox
            visibility_layout.insertWidget(visibility_layout.count() - 1, checkbox)

        self._update_graphs()

    def _on_motor_visibility_changed(self, motor_id: str) -> None:
        """Handle motor visibility toggle."""
        if self.motor_checkboxes[motor_id].isChecked():
            self.visible_motors.add(motor_id)
        else:
            self.visible_motors.discard(motor_id)
        self._update_graphs()

    def _on_time_range_changed(self, text: str) -> None:
        """Handle time range selection change."""
        self._update_graphs()

    def _on_layout_changed(self, text: str) -> None:
        """Handle layout mode change."""
        if "Single" in text:
            self.layout_mode = "single"
        else:
            self.layout_mode = "individual"
        self._update_graphs()

    @pyqtSlot()
    def update_plots(self) -> None:
        """Update plots with current buffer data."""
        self._update_graphs()

    def _get_time_range_seconds(self) -> int:
        """Get selected time range in seconds."""
        text = self.time_range_combo.currentText()
        ranges = {"30 sec": 30, "1 min": 60, "2 min": 120, "5 min": 300, "10 min": 600}
        return ranges.get(text, 120)

    def _update_graphs(self) -> None:
        """Update graph display with current data."""
        # Clear existing plots
        while self.graph_layout.count() > 0:
            widget = self.graph_layout.takeAt(0).widget()
            if widget:
                widget.deleteLater()

        self.plot_curves = {}
        self.plot_items = {}

        if self.layout_mode == "single":
            self._create_single_graph()
        else:
            self._create_individual_graphs()

    def _create_single_graph(self) -> None:
        """Create single graph with all motors."""
        plot = pg.PlotWidget(title="Motor Current Trends")
        plot.setLabel('left', 'Current', units='mA')
        plot.setLabel('bottom', 'Time')
        plot.addLegend()
        plot.enableAutoRange()

        time_range_s = self._get_time_range_seconds()
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=time_range_s)

        for motor_id in self.visible_motors:
            data = self.trend_buffer.get_data_range(motor_id, start_time, end_time)
            if data:
                timestamps, values = zip(*data)
                # Convert timestamps to seconds from start
                x_data = np.array([(ts - start_time).total_seconds() for ts in timestamps])
                y_data = np.array(values)

                color = self.motor_colors.get(motor_id, (255, 255, 255))
                curve = plot.plot(x_data, y_data, name=motor_id, pen=pg.mkPen(color=color, width=2))
                self.plot_curves[motor_id] = curve

        self.graph_layout.addWidget(plot)

    def _create_individual_graphs(self) -> None:
        """Create individual graphs for each motor."""
        time_range_s = self._get_time_range_seconds()
        end_time = datetime.now()
        start_time = end_time - timedelta(seconds=time_range_s)

        for motor_id in self.visible_motors:
            plot = pg.PlotWidget(title=motor_id)
            plot.setLabel('left', 'Current', units='mA')
            plot.setLabel('bottom', 'Time')
            plot.enableAutoRange()

            data = self.trend_buffer.get_data_range(motor_id, start_time, end_time)
            if data:
                timestamps, values = zip(*data)
                x_data = np.array([(ts - start_time).total_seconds() for ts in timestamps])
                y_data = np.array(values)

                color = self.motor_colors.get(motor_id, (255, 255, 255))
                curve = plot.plot(x_data, y_data, pen=pg.mkPen(color=color, width=2))
                self.plot_curves[motor_id] = curve

            self.plot_items[motor_id] = plot
            self.graph_layout.addWidget(plot)
