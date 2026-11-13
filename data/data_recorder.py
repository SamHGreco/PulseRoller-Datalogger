"""
Data Module: Recording Engine for Long-Term Data Storage

Independent from graph display buffers, stores all samples during recording session.
Supports extended recording (30+ minutes) with efficient memory management.

Thread-Safe: Yes (uses RLock)
"""

import logging
import csv
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class DataRecorder:
    """
    Records motor current data to memory during a recording session.
    
    Features:
    - Independent from graph display buffers
    - Full sample rate recording (no decimation)
    - Efficient memory usage for long recordings
    - CSV export with ISO timestamps
    - Thread-safe operation
    
    Data Storage Format (in-memory):
    List of (timestamp, motor_values_dict) tuples
    motor_values_dict: {motor_id: current_mA}
    """

    def __init__(self):
        """Initialize the data recorder."""
        self._recording = False
        self._start_time: Optional[datetime] = None
        self._data: List[Tuple[datetime, Dict[str, float]]] = []
        self._lock = RLock()
        logger.debug("Initialized DataRecorder")

    def start_recording(self) -> None:
        """Start a new recording session."""
        with self._lock:
            self._recording = True
            self._start_time = datetime.now()
            self._data = []
            logger.info(f"Started recording at {self._start_time}")

    def stop_recording(self) -> None:
        """Stop the current recording session."""
        with self._lock:
            if not self._recording:
                logger.warning("Attempted to stop recording when not recording")
                return

            self._recording = False
            sample_count = len(self._data)
            duration = datetime.now() - self._start_time if self._start_time else None
            logger.info(f"Stopped recording: {sample_count} samples, duration: {duration}")

    def is_recording(self) -> bool:
        """Check if currently recording."""
        with self._lock:
            return self._recording

    def add_sample(self, motor_values: Dict[str, float], timestamp: Optional[datetime] = None) -> None:
        """
        Add a sample during recording.
        
        Args:
            motor_values: Dictionary of {motor_id: current_value_mA}
            timestamp: Sample timestamp (auto-generated if not provided)
        """
        if timestamp is None:
            timestamp = datetime.now()

        with self._lock:
            if not self._recording:
                return

            # Validate motor values
            for motor_id in motor_values:
                if not isinstance(motor_values[motor_id], (int, float)):
                    logger.warning(f"Invalid data type for {motor_id}: {type(motor_values[motor_id])}")
                    return

            self._data.append((timestamp, dict(motor_values)))

    def get_recorded_data(self) -> List[Tuple[datetime, Dict[str, float]]]:
        """
        Get all recorded data.
        
        Returns:
            List of (timestamp, motor_values_dict) tuples
        """
        with self._lock:
            return list(self._data)

    def get_record_count(self) -> int:
        """Get number of samples recorded."""
        with self._lock:
            return len(self._data)

    def get_duration(self) -> Optional[float]:
        """
        Get recording duration in seconds.
        
        Returns:
            Duration in seconds or None if no data
        """
        with self._lock:
            if len(self._data) < 2:
                return None
            start = self._data[0][0]
            end = self._data[-1][0]
            return (end - start).total_seconds()

    def export_to_csv(self, filepath: Path, motor_names: Dict[str, str]) -> None:
        """
        Export recorded data to CSV file.
        
        Format:
        Timestamp,Motor1,Motor2,...
        2026-01-01 08:15:01.250,152.3,148.4,...
        
        Args:
            filepath: Destination file path
            motor_names: Mapping of {motor_id: display_name}
            
        Raises:
            IOError: If file cannot be written
        """
        with self._lock:
            data_copy = list(self._data)

        if not data_copy:
            logger.warning("No data to export")
            return

        try:
            # Extract all motor IDs from data
            motor_ids = list(data_copy[0][1].keys())
            headers = ['Timestamp'] + [motor_names.get(mid, mid) for mid in motor_ids]

            with open(filepath, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(headers)

                for timestamp, motor_values in data_copy:
                    # Format timestamp as ISO with milliseconds
                    ts_str = timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    row = [ts_str] + [motor_values.get(mid, 0.0) for mid in motor_ids]
                    writer.writerow(row)

            logger.info(f"Exported {len(data_copy)} records to {filepath}")
        except IOError as e:
            logger.error(f"Failed to export CSV: {e}")
            raise

    def clear(self) -> None:
        """Clear all recorded data."""
        with self._lock:
            self._data = []
            self._start_time = None
            logger.debug("DataRecorder cleared")
