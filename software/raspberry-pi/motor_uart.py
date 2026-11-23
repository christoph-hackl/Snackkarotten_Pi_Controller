#!/usr/bin/env python3
"""Simple UART test client for the STM32 motor co-processor.

Sends a motor command to the STM32 and prints the telemetry lines it returns.

Command format (Pi -> STM32):
    M <m1> <m2> <m3> <m4> <m5> <m6>\\r\\n      values in percent, -100 ... +100

Telemetry (STM32 -> Pi, about once per second):
    ENC <6 counts> SPD <6 counts/s> PWM <6 percent> ADC <5 raw values>
"""

import argparse
import time

import serial  # pip install pyserial

DEFAULT_PORT = "/dev/serial0"  # GPIO14 (TX) / GPIO15 (RX)
DEFAULT_BAUD = 38400           # must match USART1 config in firmware/Core/Src/main.c


def build_command(speeds):
    if len(speeds) > 6:
        raise ValueError("at most 6 motor values")
    values = [max(-100, min(100, int(v))) for v in speeds]
    values += [0] * (6 - len(values))
    return "M " + " ".join(str(v) for v in values) + "\r\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("speeds", nargs="*", type=int, default=[50, -30],
                        help="motor speeds in percent (-100..100), up to 6 values")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument("--interval", type=float, default=1.0,
                        help="seconds between commands")
    args = parser.parse_args()

    command = build_command(args.speeds)

    with serial.Serial(args.port, args.baud, timeout=0.1) as ser:
        print(f"UART open: {args.port} @ {args.baud}")
        try:
            while True:
                ser.write(command.encode())
                print("PI : " + command.strip())

                deadline = time.monotonic() + args.interval
                while time.monotonic() < deadline:
                    line = ser.readline().decode(errors="ignore").strip()
                    if line:
                        print("STM: " + line)
        except KeyboardInterrupt:
            print("\nStopping motors")
            ser.write(build_command([]).encode())


if __name__ == "__main__":
    main()
