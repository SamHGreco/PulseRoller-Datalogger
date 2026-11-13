# MDR Current Data Logger Configuration

This file documents the application configuration stored in `~/.mdr_logger/motor_config.json`.

## Default Motor Configuration

The application comes pre-configured with four motors, each with display names and corresponding PLC tag paths:

```json
{
  "motors": [
    {
      "motor_id": "motor_001",
      "name": "Motor 1 - Left MDR (Line 1)",
      "plc_tag": "ConveylinxAi2_1AOI.I_Current_Left_MDR",
      "enabled": true
    },
    {
      "motor_id": "motor_002",
      "name": "Motor 2 - Right MDR (Line 1)",
      "plc_tag": "ConveylinxAi2_1AOI.I_Current_Right_MDR",
      "enabled": true
    },
    {
      "motor_id": "motor_003",
      "name": "Motor 3 - Left MDR (Line 2)",
      "plc_tag": "ConveylinxAi2_2AOI.I_Current_Left_MDR",
      "enabled": true
    },
    {
      "motor_id": "motor_004",
      "name": "Motor 4 - Right MDR (Line 2)",
      "plc_tag": "ConveylinxAi2_2AOI.I_Current_Right_MDR",
      "enabled": true
    }
  ]
}
```

## Configuration Management

- **Location**: `~/.mdr_logger/motor_config.json` (home directory)
- **Format**: JSON
- **Auto-save**: Changes are automatically saved when motors are added, removed, edited, or enabled/disabled via the GUI
- **Persistence**: Configuration persists across application restarts

## Scaling to More Motors

The application is designed to scale to 10+ motors without code changes:

1. Use the **Motor Configuration** tab to add new motors
2. Click "Add Motor" and enter the motor name and PLC tag
3. Configuration is automatically saved
4. The application will include the new motor in:
   - Live trending display (with unique color)
   - CSV export
   - Diagnostics and health monitoring

## PLC Tag Format

PLC tags follow Allen Bradley Logix naming conventions:
- Structure: `StructureName.MemberName`
- Example: `ConveylinxAi2_1AOI.I_Current_Left_MDR`
- Data type: REAL (32-bit float, typical for current readings)
- Units: Milliamps (mA)

## Default PLC Settings

The application writes speed control to:
- **Tag**: `MDR_Speed_Setting`
- **Data Type**: DINT (32-bit signed integer)
- **Range**: 0-100 (configurable in SpeedControlTab)
