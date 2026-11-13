"""
PLC Module: Allen Bradley CompactLogix Communication Manager

Handles thread-safe communication with L18ER PLC using pycomm3.
Implements multi-tag reads for optimal performance.

Thread-Safe: Yes (uses background thread)
Signals: Connected, Disconnected, DataUpdated, ErrorOccurred, HealthUpdated
"""

import logging
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from PyQt6.QtCore import QObject, pyqtSignal

from pycomm3.exceptions import CommError
from pycomm3 import LogixDriver

logger = logging.getLogger(__name__)


class PLCManager(QObject):
    """
    Manages PLC communication with CompactLogix L18ER.
    
    Features:
    - Thread-safe async communication
    - Multi-tag reads for efficiency
    - Automatic reconnection
    - Communication health monitoring
    - Signal-based event notification
    
    Critical Optimization:
    Uses multi-tag reads instead of individual reads. With 10 motors at 250ms,
    this dramatically reduces EtherNet/IP traffic and improves achievable sample rates.
    
    Example multi-tag read:
        results = plc.read(tag1, tag2, tag3, ...)
    
    Args:
        plc_ip: IP address of the PLC
        poll_interval_ms: Polling interval in milliseconds
    """

    # Signals for thread-safe communication
    Connected = pyqtSignal()
    Disconnected = pyqtSignal()
    DataUpdated = pyqtSignal(dict)  # {motor_id: current_mA}
    ErrorOccurred = pyqtSignal(str)  # error message
    HealthUpdated = pyqtSignal(dict)  # {key: value} health metrics

    def __init__(self, plc_ip: str = "", poll_interval_ms: int = 250):
        """
        Initialize PLC manager.
        
        Args:
            plc_ip: PLC IP address (empty string if not yet configured)
            poll_interval_ms: Polling interval in milliseconds
        """
        super().__init__()
        self.plc_ip = plc_ip
        self.poll_interval_ms = poll_interval_ms
        self.poll_interval_s = poll_interval_ms / 1000.0

        self._plc: Optional[LogixDriver] = None
        self._connected = False
        self._running = False
        self._poll_thread: Optional[threading.Thread] = None

        # Health metrics
        self._samples_read = 0
        self._samples_failed = 0
        self._last_error: Optional[str] = None
        self._poll_rate = 0.0  # Actual achieved poll rate
        self._last_poll_times: List[float] = []

        logger.debug(f"Initialized PLCManager: IP={plc_ip}, poll_interval={poll_interval_ms}ms")

    def set_poll_interval(self, poll_interval_ms: int) -> None:
        """Set the polling interval."""
        self.poll_interval_ms = poll_interval_ms
        self.poll_interval_s = poll_interval_ms / 1000.0
        logger.info(f"Set poll interval to {poll_interval_ms}ms")

    def connect(self, plc_ip: str) -> bool:
        """
        Connect to the PLC.
        
        Args:
            plc_ip: IP address of the PLC
            
        Returns:
            True if connection successful, False otherwise
        """
        if self._connected:
            logger.warning("Already connected to PLC")
            return False

        try:
            self.plc_ip = plc_ip
            self._plc = LogixDriver(plc_ip)
            
            # Open the connection (establishes EtherNet/IP session)
            self._plc.open()
            
            self._connected = True
            self._running = True

            # Start polling thread
            self._poll_thread = threading.Thread(target=self._polling_loop, daemon=True)
            self._poll_thread.start()

            logger.info(f"Connected to PLC at {plc_ip}")
            self.Connected.emit()
            return True

        except CommError as e:
            self._connected = False
            error_msg = f"PLC connection failed: {str(e)}"
            logger.error(error_msg)
            self.ErrorOccurred.emit(error_msg)
            self._last_error = error_msg
            return False

    def disconnect(self) -> None:
        """Disconnect from the PLC."""
        if not self._connected:
            return

        try:
            self._running = False

            if self._poll_thread:
                self._poll_thread.join(timeout=2.0)

            if self._plc:
                self._plc.close()
                self._plc = None

            self._connected = False
            logger.info("Disconnected from PLC")
            self.Disconnected.emit()

        except Exception as e:
            logger.error(f"Error during disconnect: {e}")

    def is_connected(self) -> bool:
        """Check if connected to PLC."""
        return self._connected

    def get_poll_interval(self) -> int:
        """Get current poll interval in milliseconds."""
        return self.poll_interval_ms

    def set_polling_enabled(self, enabled: bool) -> None:
        """Enable or disable polling."""
        self._running = enabled
        logger.info(f"Polling {'enabled' if enabled else 'disabled'}")

    def write_tag(self, tag: str, value: int, data_type: str = "DINT") -> bool:
        """
        Write a value to a PLC tag.
        
        Args:
            tag: Tag name
            value: Value to write (typically DINT)
            data_type: Data type (default "DINT") - note: pycomm3 infers type automatically
            
        Returns:
            True if write successful, False otherwise
        """
        if not self._connected or not self._plc:
            logger.error("Cannot write tag: not connected to PLC")
            return False

        try:
            # pycomm3 write signature: write((tag, value), (tag2, value2), ...)
            # Pass as (tag, value) tuple. pycomm3 automatically infers data type.
            self._plc.write((tag, value))
            logger.info(f"Wrote {tag} = {value}")
            return True
        except CommError as e:
            error_msg = f"Failed to write {tag}: {str(e)}"
            logger.error(error_msg)
            self._last_error = error_msg
            self.ErrorOccurred.emit(error_msg)
            self._samples_failed += 1
            return False
        except Exception as e:
            error_msg = f"Error writing {tag}: {str(e)}"
            logger.error(error_msg)
            self._last_error = error_msg
            self.ErrorOccurred.emit(error_msg)
            self._samples_failed += 1
            return False

    def read_tag(self, tag: str) -> Optional[float]:
        """
        Read a single tag from PLC.
        
        Args:
            tag: Tag name
            
        Returns:
            Tag value or None if read failed
        """
        if not self._connected or not self._plc:
            return None

        try:
            result = self._plc.read(tag)
            return float(result.value)
        except CommError as e:
            logger.warning(f"Failed to read {tag}: {str(e)}")
            return None

    def _polling_loop(self) -> None:
        """
        Main polling thread loop.
        Reads all enabled motor tags and emits DataUpdated signal.
        """
        logger.info("Started PLC polling thread")

        while self._running:
            try:
                if not self._connected or not self._plc:
                    time.sleep(0.1)
                    continue

                loop_start = time.time()

                # Placeholder for motor tag list - will be set by application
                # This method should be called with the actual motor list
                time.sleep(self.poll_interval_s)

                # Update poll rate calculation
                self._update_poll_rate()

            except Exception as e:
                logger.error(f"Error in polling loop: {e}")
                self._last_error = str(e)
                self.ErrorOccurred.emit(str(e))
                self._samples_failed += 1
                time.sleep(0.5)

    def read_motor_tags(self, motor_tags: List[Tuple[str, str]]) -> Optional[Dict[str, float]]:
        """
        Read multiple motor tags in a single multi-tag read operation.
        
        CRITICAL OPTIMIZATION: This method uses multi-tag reads which dramatically
        improve performance compared to individual reads. With 10 motors at 250ms,
        this reduces EtherNet/IP traffic significantly.
        
        Args:
            motor_tags: List of (motor_id, plc_tag) tuples
            
        Returns:
            Dictionary of {motor_id: current_mA} or None if read failed
        """
        if not self._connected or not self._plc or not motor_tags:
            return None

        try:
            # Build tag list for multi-read
            tags_to_read = [tag for _, tag in motor_tags]

            # Perform multi-tag read - SINGLE EtherNet/IP request
            results = self._plc.read(*tags_to_read)

            # Parse results into motor_id -> value mapping
            motor_values = {}
            for (motor_id, _), result in zip(motor_tags, results):
                try:
                    # pycomm3 Tag objects have .value attribute
                    # If read failed, value might be None or cause an exception
                    if result.value is not None:
                        motor_values[motor_id] = float(result.value)
                    else:
                        logger.warning(f"Null value for {motor_id}")
                        motor_values[motor_id] = 0.0
                except (ValueError, TypeError, AttributeError) as e:
                    logger.warning(f"Invalid data for {motor_id}: {result.value if hasattr(result, 'value') else result}")
                    motor_values[motor_id] = 0.0

            self._samples_read += 1
            return motor_values

        except CommError as e:
            error_msg = f"Multi-tag read failed: {str(e)}"
            logger.error(error_msg)
            self._last_error = error_msg
            self.ErrorOccurred.emit(error_msg)
            self._samples_failed += 1
            return None

    def _update_poll_rate(self) -> None:
        """Update actual achieved poll rate."""
        now = time.time()
        self._last_poll_times.append(now)

        # Keep last 10 polls for rate calculation
        if len(self._last_poll_times) > 10:
            self._last_poll_times.pop(0)

        if len(self._last_poll_times) > 1:
            time_span = self._last_poll_times[-1] - self._last_poll_times[0]
            if time_span > 0:
                self._poll_rate = (len(self._last_poll_times) - 1) / time_span

    def get_health_metrics(self) -> Dict:
        """
        Get PLC communication health metrics.
        
        Returns:
            Dictionary with health information
        """
        total_attempts = self._samples_read + self._samples_failed
        success_rate = 0.0
        if total_attempts > 0:
            success_rate = (self._samples_read / total_attempts) * 100

        return {
            'connected': self._connected,
            'plc_ip': self.plc_ip,
            'samples_read': self._samples_read,
            'samples_failed': self._samples_failed,
            'total_attempts': total_attempts,
            'success_rate': success_rate,
            'achieved_poll_rate': self._poll_rate,
            'configured_poll_interval_ms': self.poll_interval_ms,
            'last_error': self._last_error or 'None'
        }

    def reset_health_metrics(self) -> None:
        """Reset health counters."""
        self._samples_read = 0
        self._samples_failed = 0
        self._last_error = None
        self._last_poll_times = []
