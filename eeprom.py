# AT25010B SPI EEPROM driver (128 bytes) for Raspberry Pi Pico 2 / MicroPython
from machine import SPI, Pin
import time

SIZE = 128  # bytes
PAGE = 8    # page size in bytes

# Opcodes
WREN = 0x06
RDSR = 0x05
READ = 0x03
WRITE = 0x02


class AT25010B:
    def __init__(self):
        self.cs = Pin(17, Pin.OUT, value=1)
        self.spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
                       sck=Pin(18), mosi=Pin(19), miso=Pin(16))

    def _status(self):
        self.cs(0)
        self.spi.write(bytes([RDSR]))
        s = self.spi.read(1)[0]
        self.cs(1)
        return s

    def _wait_ready(self, timeout_ms=20):
        t = time.ticks_ms()
        while self._status() & 0x01:  # RDY/BSY bit
            if time.ticks_diff(time.ticks_ms(), t) > timeout_ms:
                raise OSError("EEPROM write timeout")

    def read(self):
        self.cs(0)
        self.spi.write(bytes([READ, 0x00]))
        data = self.spi.read(SIZE)
        self.cs(1)
        return bytearray(data)

    def write(self, data):
        # Page-wise, never crossing a page boundary
        for addr in range(0, SIZE, PAGE):
            self.cs(0)
            self.spi.write(bytes([WREN]))
            self.cs(1)
            self.cs(0)
            self.spi.write(bytes([WRITE, addr]) + bytes(data[addr:addr + PAGE]))
            self.cs(1)
            self._wait_ready()
