"""
Data Module: Circular Buffer for Memory-Efficient Time-Series Storage

Implements a fixed-size circular buffer with timestamp and multi-motor data storage.
Used for graph display to keep memory usage constant regardless of runtime duration.

Thread-Safe: Yes (uses RLock)
"""

import logging
from collections import deque
from datetime import datetime
from threading import RLock
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TrendBuffer:
    """
    Circular buffer for storing trend data with memory-efficient operation.
    
    Features:
    - Fixed-size memory footprint
    - FIFO eviction when buffer full
    - Thread-safe access
    - Multi-motor data support
    - Timestamp tracking
    
    The buffer stores tuples of (timestamp, motor_values_dict) where motor_values_dict
    contains {motor_id: current_value_mA} for all motors at that sample time.
    
    Args:
        max_samples: Maximum number of samples to retain
        motor_ids: List of motor IDs that will be stored
    """

    def __init__(self, max_samples: int = 8000, motor_ids: Optional[List[str]] = None):
        """
        Initialize the trend buffer.
        
        Args:
            max_samples: Maximum samples to retain (default 8000 ~= 2 min @ 250ms + display overhead)
            motor_ids: List of motor IDs for initialization
        """
        self.max_samples = max_samples
        self.motor_ids = motor_ids or []
        self._buffer: deque = deque(maxlen=max_samples)
        self._lock = RLock()
        logger.debug(f"Initialized TrendBuffer: max_samples={max_samples}, motors={len(self.motor_ids)}")

    def add_sample(self, motor_values: Dict[str, float], timestamp: Optional[datetime] = None) -> None:
        """
        Add a sample to the buffer.
        
        Args:
            motor_values: Dictionary of {motor_id: current_value_mA}
            timestamp: Sample timestamp (auto-generated if not provided)
        """
        if timestamp is None:
            timestamp = datetime.now()

        with self._lock:
            # Validate motor values
            for motor_id in motor_values:
                if not isinstance(motor_values[motor_id], (int, float)):
                    logger.warning(f"Invalid data type for {motor_id}: {type(motor_values[motor_id])}")
                    return

            self._buffer.append((timestamp, dict(motor_values)))
            
            if len(self._buffer) >= self.max_samples * 0.95:
                logger.debug(f"TrendBuffer approaching capacity: {len(self._buffer)}/{self.max_samples}")

    def get_all_data(self) -> List[Tuple[datetime, Dict[str, float]]]:
        """
        Get all data in the buffer.
        
        Returns:
            List of (timestamp, motor_values_dict) tuples
        """
        with self._lock:
            return list(self._buffer)

    def get_data_for_motor(self, motor_id: str) -> List[Tuple[datetime, float]]:
        """
        Get time series data for a specific motor.
        
        Args:
            motor_id: ID of motor to retrieve
            
        Returns:
            List of (timestamp, current_mA) tuples
        """
        with self._lock:
            return [(ts, values.get(motor_id, 0.0)) for ts, values in self._buffer]

    def get_data_range(self, motor_id: str, start_time: datetime, 
                      end_time: datetime) -> List[Tuple[datetime, float]]:
        """
        Get data for a specific motor within a time range.
        
        Args:
            motor_id: ID of motor
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Filtered list of (timestamp, current_mA) tuples
        """
        with self._lock:
            return [
                (ts, values.get(motor_id, 0.0))
                for ts, values in self._buffer
                if start_time <= ts <= end_time
            ]

    def get_latest_values(self) -> Optional[Dict[str, float]]:
        """
        Get the most recent sample values for all motors.
        
        Returns:
            Dictionary of {motor_id: current_mA} or None if buffer empty
        """
        with self._lock:
            if self._buffer:
                return dict(self._buffer[-1][1])
            return None

    def get_latest_timestamp(self) -> Optional[datetime]:
        """Get timestamp of the most recent sample."""
        with self._lock:
            if self._buffer:
                return self._buffer[-1][0]
            return None

    def clear(self) -> None:
        """Clear all data from the buffer."""
        with self._lock:
            self._buffer.clear()
            logger.info("TrendBuffer cleared")

    def get_size(self) -> int:
        """Get current number of samples in buffer."""
        with self._lock:
            return len(self._buffer)

    def get_capacity_percentage(self) -> float:
        """Get buffer capacity as percentage."""
        with self._lock:
            return (len(self._buffer) / self.max_samples) * 100 if self.max_samples > 0 else 0
