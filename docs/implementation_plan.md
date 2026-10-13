# Implementation Plan – EEPROM_tool (v0.1)

## Goal
A minimal MicroPython program on a Raspberry Pi Pico 2 that reads, writes and verifies
an AT25010B SPI EEPROM (128 bytes) through a numbered console menu. The program keeps
an internal **state array** (128 bytes, initialized to `00`) shown and edited as hex dump.

## Decisions (agreed)
- **Display:** every menu cycle prints the menu options, followed by the current state as hex dump.
- **READ:** EEPROM content replaces the state array.
- **MODIFY:** one line `ADDR: B0 B1 ...` (hex), **1 to 16 bytes** of arbitrary length,
  e.g. `10: DE AD BE EF`. Rejected with a message if: invalid hex, >16 bytes, 0 bytes,
  or `ADDR + count > 128`. One entry per MODIFY, then back to the menu (updated dump is shown there).

## Proposed Changes

### Repository layout
```
EEPROM_tool/
├── eeprom.py     # AT25010B driver (SPI)
├── main.py       # menu loop, state array, hex dump helpers
└── README.md     # from README_draft.md
```

---

#### [NEW] eeprom.py
Small driver class, SPI0 on GP16–19, mode 0, 1 MHz (conservative).

```python
from machine import SPI, Pin
import time

SIZE = 128
PAGE = 8
WREN, RDSR, READ, WRITE = 0x06, 0x05, 0x03, 0x02

class AT25010B:
    def __init__(self):
        self.cs = Pin(17, Pin.OUT, value=1)
        self.spi = SPI(0, baudrate=1_000_000, polarity=0, phase=0,
                       sck=Pin(18), mosi=Pin(19), miso=Pin(16))

    def _status(self):
        self.cs(0); self.spi.write(bytes([RDSR])); s = self.spi.read(1)[0]; self.cs(1)
        return s

    def _wait_ready(self, timeout_ms=20):
        t = time.ticks_ms()
        while self._status() & 0x01:          # RDY/BSY bit
            if time.ticks_diff(time.ticks_ms(), t) > timeout_ms:
                raise OSError("EEPROM write timeout")

    def read(self):
        self.cs(0); self.spi.write(bytes([READ, 0x00])); data = self.spi.read(SIZE); self.cs(1)
        return bytearray(data)

    def write(self, data):
        for addr in range(0, SIZE, PAGE):     # page-wise, never cross page boundary
            self.cs(0); self.spi.write(bytes([WREN])); self.cs(1)
            self.cs(0); self.spi.write(bytes([WRITE, addr]) + data[addr:addr+PAGE]); self.cs(1)
            self._wait_ready()
```

---

#### [NEW] main.py
```python
from eeprom import AT25010B, SIZE

def dump(buf):                      # 16 bytes per line: "00: 00 00 ..."
    for a in range(0, SIZE, 16):
        print("{:02X}: ".format(a) + " ".join("{:02X}".format(b) for b in buf[a:a+16]))

def modify(state):                  # one line "ADDR: B0 B1 ..." with 1..16 bytes
    line = input("ADDR: B0 B1 ... (max 16 bytes) > ")
    try:
        a, rest = line.split(":", 1)
        addr = int(a, 16)
        vals = [int(x, 16) for x in rest.split()]
        if not 1 <= len(vals) <= 16 or any(v > 0xFF for v in vals) \
           or addr < 0 or addr + len(vals) > SIZE:
            raise ValueError
    except ValueError:
        print("Invalid input"); return
    state[addr:addr+len(vals)] = bytes(vals)

def main():
    ee = AT25010B()
    state = bytearray(SIZE)         # all 0x00
    while True:
        print("\n1 READ  2 MODIFY  3 WRITE  4 VERIFY  5 EXIT\n")
        dump(state)                 # current state below the menu
        c = input("> ").strip()
        if c == "1": state[:] = ee.read(); print("Read done.")
        elif c == "2": modify(state)
        elif c == "3": ee.write(state); print("Written.")
        elif c == "4": verify(ee, state)   # prints OK or list of mismatching addresses
        elif c == "5": break
        else: print("Invalid choice")

main()
```
- **VERIFY:** reads EEPROM, compares with state, prints `VERIFY OK` or lines `ADDR: eeprom=XX state=YY`.
- **WRITE:** writes all 128 bytes (16 pages × 8 bytes, ~80 ms max).

---

#### [NEW] README.md
Content of `README_draft.md`, plus filled "Usage" (menu description) and "Development setup" (MicroPico / mpremote).

## Verification Plan

### Manual (on hardware)
1. Upload `eeprom.py` and `main.py` via MicroPico (or `mpremote cp eeprom.py main.py :`), run `main.py`.
2. `4 VERIFY` on a blank chip → expect mismatches (chip is FF, state is 00).
3. `2 MODIFY` → `00: 01 02 03 04`, `3 WRITE`, `4 VERIFY` → `VERIFY OK`.
4. Power-cycle Pico, `1 READ` → first bytes `01 02 03 04`, rest as before.
5. Enter invalid menu input / invalid hex → error message, no crash.
