# mcp_adc.py
import spidev

class MCP3208:
    def __init__(self, bus=0, device=0):
        """
        Initializes the MCP3208 ADC on a specific SPI bus and device.
        """
        self.spi = spidev.SpiDev()
        self.spi.open(bus, device)
        self.spi.max_speed_hz = 1350000 # Set SPI clock speed
        print("MCP3208 ADC Initialized.")

    def read_channel(self, channel):
        """
        Reads a single analog channel (0-7).
        Returns a 12-bit value (0-4095).
        """
        if channel < 0 or channel > 7:
            return -1
        
        # MCP3208 requires a 3-byte command
        # Byte 1: 0000 0001 (Start Bit)
        # Byte 2: 1_SGL_D2_D1_D0_0_0_0 (SGL=1 for single-ended, D2-D0 is channel)
        # Byte 3: 0000 0000 (Don't care)
        cmd1 = 1
        cmd2 = (8 + channel) << 4
        cmd3 = 0

        resp = self.spi.xfer2([cmd1, cmd2, cmd3])
        
        # Parse the 12-bit result
        # Byte 2 (resp[1]) contains bits 11-8 (masked with 0x0F)
        # Byte 3 (resp[2]) contains bits 7-0
        adc_val = ((resp[1] & 3) << 8) + resp[2]
        return adc_val

    def cleanup(self):
        """Closes the SPI connection."""
        self.spi.close()
        print("MCP3208 ADC closed.")