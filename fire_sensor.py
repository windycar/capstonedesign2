# fire_sensor.py
class FireSensor:
    FLAME_CHANNEL = 0 # MCP3208 Channel 0
    FLAME_THRESHOLD = 800 # Example threshold (0-4095), needs calibration!

    def __init__(self, adc):
        """
        Initializes the Flame Sensor.
        adc: An initialized MCP3208 object.
        """
        self.adc = adc
        self.is_detected = False
        print("FireSensor Initialized.")

    def read_value(self):
        """Reads and updates the flame detection state."""
        value = self.adc.read_channel(self.FLAME_CHANNEL)
        
        if value > self.FLAME_THRESHOLD:
            self.is_detected = True
        else:
            self.is_detected = False
            
        return value, self.is_detected

    def cleanup(self):
        pass