# gas_sensor.py
class GasSensor:
    GAS_CHANNEL = 1 # MCP3208 Channel 1
    GAS_THRESHOLD = 700 # Example threshold (0-4095), needs calibration!

    def __init__(self, adc):
        """
        Initializes the Gas Sensor.
        adc: An initialized MCP3208 object.
        """
        self.adc = adc
        self.is_detected = False
        print("GasSensor Initialized.")

    def read_value(self):
        """Reads and updates the gas detection state."""
        value = self.adc.read_channel(self.GAS_CHANNEL)
        
        if value > self.GAS_THRESHOLD:
            self.is_detected = True
        else:
            self.is_detected = False
            
        return value, self.is_detected

    def cleanup(self):
        pass # Nothing to clean up, MCP is cleaned in main