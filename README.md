# EEPROM_tool

Read, write and verify an **AT25010B** SPI EEPROM (128 bytes) using a
**Raspberry Pi Pico 2** running **MicroPython**.

## Hardware

- Raspberry Pi Pico 2 (RP2350) with MicroPython
- AT25010B EEPROM (1 Kbit = 128 × 8 bit, SPI)
- Supply: 3.3 V from the Pico

## Pinout

The connection uses the Pico's hardware **SPI0** bus.

| AT25010B pin | Signal | Direction (from Pico) | Pico 2 GPIO | Pico 2 physical pin |
|:---:|:---|:---:|:---:|:---:|
| 1 | CS (chip select, active low) | out | GP17 (SPI0 CSn) | 22 |
| 2 | SO (serial out) | in | GP16 (SPI0 RX / MISO) | 21 |
| 3 | WP (write protect, active low) | – | tie to 3V3 | 36 |
| 4 | GND | – | GND | 23 |
| 5 | SI (serial in) | out | GP19 (SPI0 TX / MOSI) | 25 |
| 6 | SCK (serial clock) | out | GP18 (SPI0 SCK) | 24 |
| 7 | HOLD (active low) | – | tie to 3V3 | 36 |
| 8 | VCC | – | 3V3 (OUT) | 36 |

> Put a 100 nF decoupling capacitor between VCC and GND close to the EEPROM.

## Data format

Memory content is handled as a byte array of 128 bytes. The user works with
**hex dump text**: bytes written as two hex digits `00`–`FF`, separated by spaces.

```
00: FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
10: FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
...
70: FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF FF
```

The program keeps an internal **state array** of 128 bytes, initialized to `00`.

## Usage

Run `main.py` on the Pico. The menu is shown, followed by the current state:

```
1 READ  2 MODIFY  3 WRITE  4 VERIFY  5 EXIT

00: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
...
70: 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00
>
```

Enter the menu number:

| No. | Option | Action |
|:---:|:---|:---|
| 1 | READ | Read the whole EEPROM into the state array |
| 2 | MODIFY | Change bytes in the state array (see below) |
| 3 | WRITE | Write the state array to the EEPROM |
| 4 | VERIFY | Compare EEPROM with state; prints `VERIFY OK` or the mismatching addresses |
| 5 | EXIT | Leave the program |

### MODIFY input

One line: start address, colon, then **1 to 16** bytes, all in hex:

```
ADDR: B0 B1 ...
10: DE AD BE EF
```

This writes `DE AD BE EF` into the state at addresses `0x10`–`0x13`.
Invalid hex, more than 16 bytes, or addresses beyond `0x7F` are rejected.

## Development setup

1. Flash MicroPython (**RP2350** build) onto the Pico 2.
2. Install the **MicroPico** extension in Antigravity (`paulober.pico-w-go`).
3. Connect the Pico via USB, upload `eeprom.py` and `main.py`, run `main.py`.

Alternative via command line ([mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html)):

```bash
pip install mpremote
mpremote cp eeprom.py main.py :
mpremote run main.py
```
