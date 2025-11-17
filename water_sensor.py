# water_sensor.py
class WaterSensor:
    WATER_CHANNEL = 2 # MCP3208 Channel 2
    WATER_THRESHOLD = 500 # Example threshold (0-4095), needs calibration!

    def __init__(self, adc):
        """
        Initializes the Water Level Sensor.
        adc: An initialized MCP3208 object.
        """
        self.adc = adc
        self.water_level_percent = 100 # Assume full at start
        print("WaterSensor Initialized.")

    def read_level(self):
        """
        Reads the water level and converts it to a percentage (0-100).
        0 = Empty, 100 = Full.
        This logic depends heavily on your sensor.
        """
        value = self.adc.read_channel(self.WATER_CHANNEL)
        
        # Example conversion: (Assumes value increases as water level drops)
        # This needs to be calibrated based on your sensor's min/max readings.
        MIN_READING = 100 # Dummy value for "Full"
        MAX_READING = 1000 # Dummy value for "Empty"

        if value >= MAX_READING:
            self.water_level_percent = 0
        elif value <= MIN_READING:
            self.water_level_percent = 100
        else:
            self.water_level_percent = 100 - int(((value - MIN_READING) / (MAX_READING - MIN_READING)) * 100)
            
        return self.water_level_percent

    def cleanup(self):
        pass