"""
Core Module: Motor Configuration Management

Handles all motor definitions, storage, and validation.
Provides a centralized interface for motor configuration state.

Thread-Safe: Yes (uses locks for config access)
"""

import json
import logging
from pathlib import Path
from dataclasses import dataclass, asdict, field
from typing import Dict, List, Optional
from threading import RLock

logger = logging.getLogger(__name__)


@dataclass
class Motor:
    """
    Represents a single Motor Driven Roller motor.
    
    Attributes:
        name: Display name for the motor
        plc_tag: Allen Bradley tag path in PLC
        enabled: Whether to include in polling
        motor_id: Unique identifier
    """
    name: str
    plc_tag: str
    enabled: bool = True
    motor_id: str = field(default_factory=lambda: "")

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'Motor':
        """Deserialize from dictionary."""
        return cls(**data)


class MotorConfigManager:
    """
    Manages motor configuration, persistence, and validation.
    
    Features:
    - Load/save motor configurations from JSON
    - Add/remove/update motors
    - Validate motor data
    - Thread-safe access to configuration
    
    Configuration File Format:
    {
        "motors": [
            {
                "motor_id": "motor_001",
                "name": "Left MDR - Line 1",
                "plc_tag": "ConveylinxAi2_1AOI.I_Current_Left_MDR",
                "enabled": true
            },
            ...
        ]
    }
    """

    CONFIG_DIR = Path.home() / '.mdr_logger'
    CONFIG_FILE = CONFIG_DIR / 'motor_config.json'
    DEFAULT_MOTORS = [
        Motor(
            motor_id='motor_001',
            name='Motor 1 - Left MDR (Line 1)',
            plc_tag='ConveylinxAi2_1AOI.I_Current_Left_MDR',
            enabled=True
        ),
        Motor(
            motor_id='motor_002',
            name='Motor 2 - Right MDR (Line 1)',
            plc_tag='ConveylinxAi2_1AOI.I_Current_Right_MDR',
            enabled=True
        ),
        Motor(
            motor_id='motor_003',
            name='Motor 3 - Left MDR (Line 2)',
            plc_tag='ConveylinxAi2_2AOI.I_Current_Left_MDR',
            enabled=True
        ),
        Motor(
            motor_id='motor_004',
            name='Motor 4 - Right MDR (Line 2)',
            plc_tag='ConveylinxAi2_2AOI.I_Current_Right_MDR',
            enabled=True
        ),
    ]

    def __init__(self):
        """Initialize motor configuration manager."""
        self._motors: Dict[str, Motor] = {}
        self._lock = RLock()
        self._load_or_create_config()

    def _load_or_create_config(self) -> None:
        """Load configuration from file or create defaults."""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        if self.CONFIG_FILE.exists():
            try:
                self.load_from_file()
                logger.info(f"Loaded motor configuration from {self.CONFIG_FILE}")
            except Exception as e:
                logger.error(f"Failed to load config file: {e}. Using defaults.")
                self._reset_to_defaults()
        else:
            self._reset_to_defaults()
            self.save_to_file()
            logger.info("Created default motor configuration")

    def _reset_to_defaults(self) -> None:
        """Reset configuration to defaults."""
        with self._lock:
            self._motors = {motor.motor_id: motor for motor in self.DEFAULT_MOTORS}

    def load_from_file(self) -> None:
        """Load motor configuration from JSON file."""
        with open(self.CONFIG_FILE, 'r') as f:
            data = json.load(f)

        with self._lock:
            self._motors = {}
            for motor_data in data.get('motors', []):
                motor = Motor.from_dict(motor_data)
                self._motors[motor.motor_id] = motor

    def save_to_file(self) -> None:
        """Save motor configuration to JSON file."""
        with self._lock:
            data = {
                'motors': [motor.to_dict() for motor in self._motors.values()]
            }

        self.CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved motor configuration to {self.CONFIG_FILE}")

    def add_motor(self, name: str, plc_tag: str, motor_id: Optional[str] = None) -> str:
        """
        Add a new motor to the configuration.
        
        Args:
            name: Display name
            plc_tag: PLC tag path
            motor_id: Optional unique ID; auto-generated if not provided
            
        Returns:
            motor_id of the newly added motor
        """
        if motor_id is None:
            motor_id = self._generate_motor_id()

        self._validate_motor_data(name, plc_tag)

        with self._lock:
            if motor_id in self._motors:
                raise ValueError(f"Motor ID {motor_id} already exists")

            motor = Motor(motor_id=motor_id, name=name, plc_tag=plc_tag, enabled=True)
            self._motors[motor_id] = motor

        self.save_to_file()
        logger.info(f"Added motor: {motor_id} - {name}")
        return motor_id

    def remove_motor(self, motor_id: str) -> None:
        """Remove a motor from configuration."""
        with self._lock:
            if motor_id not in self._motors:
                raise ValueError(f"Motor ID {motor_id} not found")
            del self._motors[motor_id]

        self.save_to_file()
        logger.info(f"Removed motor: {motor_id}")

    def update_motor(self, motor_id: str, name: Optional[str] = None,
                     plc_tag: Optional[str] = None, enabled: Optional[bool] = None) -> None:
        """
        Update a motor's configuration.
        
        Args:
            motor_id: ID of motor to update
            name: New display name (optional)
            plc_tag: New PLC tag (optional)
            enabled: New enabled state (optional)
        """
        with self._lock:
            if motor_id not in self._motors:
                raise ValueError(f"Motor ID {motor_id} not found")

            motor = self._motors[motor_id]

            if name is not None:
                self._validate_motor_data(name, motor.plc_tag)
                motor.name = name

            if plc_tag is not None:
                self._validate_motor_data(motor.name, plc_tag)
                motor.plc_tag = plc_tag

            if enabled is not None:
                motor.enabled = enabled

        self.save_to_file()
        logger.info(f"Updated motor: {motor_id}")

    def get_motor(self, motor_id: str) -> Optional[Motor]:
        """Get a motor by ID."""
        with self._lock:
            return self._motors.get(motor_id)

    def get_all_motors(self) -> List[Motor]:
        """Get list of all motors."""
        with self._lock:
            return list(self._motors.values())

    def get_enabled_motors(self) -> List[Motor]:
        """Get list of enabled motors."""
        with self._lock:
            return [m for m in self._motors.values() if m.enabled]

    def get_motor_names(self) -> Dict[str, str]:
        """Get mapping of motor_id to display name."""
        with self._lock:
            return {mid: m.name for mid, m in self._motors.items()}

    def _generate_motor_id(self) -> str:
        """Generate a unique motor ID."""
        with self._lock:
            count = len(self._motors)
            for i in range(1, 1000):
                motor_id = f"motor_{i:03d}"
                if motor_id not in self._motors:
                    return motor_id
        raise RuntimeError("Could not generate unique motor ID")

    @staticmethod
    def _validate_motor_data(name: str, plc_tag: str) -> None:
        """Validate motor data."""
        if not name or not name.strip():
            raise ValueError("Motor name cannot be empty")
        if not plc_tag or not plc_tag.strip():
            raise ValueError("PLC tag cannot be empty")
        if len(name) > 100:
            raise ValueError("Motor name too long")
        if len(plc_tag) > 256:
            raise ValueError("PLC tag too long")
