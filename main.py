# EEPROM_tool: read, modify, write and verify an AT25010B via console menu
from eeprom import AT25010B, SIZE


def dump(buf):
    # 16 bytes per line: "00: 00 00 ..."
    for a in range(0, SIZE, 16):
        print("{:02X}: ".format(a) + " ".join("{:02X}".format(b) for b in buf[a:a + 16]))


def modify(state):
    # One line "ADDR: B0 B1 ..." with 1..16 bytes
    line = input("ADDR: B0 B1 ... (max 16 bytes) > ")
    try:
        a, rest = line.split(":", 1)
        addr = int(a, 16)
        vals = [int(x, 16) for x in rest.split()]
        if not 1 <= len(vals) <= 16 or any(v < 0 or v > 0xFF for v in vals) \
                or addr < 0 or addr + len(vals) > SIZE:
            raise ValueError
    except ValueError:
        print("Invalid input")
        return
    state[addr:addr + len(vals)] = bytes(vals)


def verify(ee, state):
    data = ee.read()
    errors = 0
    for a in range(SIZE):
        if data[a] != state[a]:
            print("{:02X}: eeprom={:02X} state={:02X}".format(a, data[a], state[a]))
            errors += 1
    if errors:
        print("VERIFY FAILED ({} mismatches)".format(errors))
    else:
        print("VERIFY OK")


def main():
    ee = AT25010B()
    state = bytearray(SIZE)  # all 0x00
    while True:
        print("\n1 READ  2 MODIFY  3 WRITE  4 VERIFY  5 EXIT\n")
        dump(state)
        c = input("> ").strip()
        try:
            if c == "1":
                state[:] = ee.read()
                print("Read done.")
            elif c == "2":
                modify(state)
            elif c == "3":
                ee.write(state)
                print("Written.")
            elif c == "4":
                verify(ee, state)
            elif c == "5":
                break
            else:
                print("Invalid choice")
        except OSError as e:
            print("Error:", e)


main()
