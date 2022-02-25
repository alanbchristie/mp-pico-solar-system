"""The real-time solar-system display.
"""
try:
    from typing import Dict, List, Optional, Tuple, Union
except ImportError:
    pass

# pylint: disable=import-error
from machine import ADC, I2C, Pin, Timer  # type: ignore

# Our modules
from rtc import RTC, RealTimeClock
from planets import coordinates

# Configured I2C controller and its GPIO pins.
# The Pico Explorer uss GPIO 20/21 for SDA/SCL (I2C 0)
_I2C_ID: int = 0
_SDA: int = 20
_SCL: int = 21

# A MicroPython I2C object
_I2C: I2C = I2C(id=_I2C_ID, scl=Pin(_SCL), sda=Pin(_SDA))
_DEVICE_ADDRESSES: List[int] = _I2C.scan()

# Do we have a Real-Time Clock (at 0x52)?
_RTC_ADDRESS: Optional[int] = None
if 0x52 in _DEVICE_ADDRESSES:
    _RTC_ADDRESS = 0x52
if _RTC_ADDRESS:
    print(f'RTC device={hex(_RTC_ADDRESS)}')
else:
    print('RTC (not found)')
assert _RTC_ADDRESS

# Our RTC object (RV3028 wrapper).
_RTC: RTC = RTC(_SDA, _SCL)

# Get planet positions, now...
now: RealTimeClock = _RTC.datetime()
print(now)
p_coords: List[Tuple[float, float, float]] =\
    coordinates(now.year, now.month, now.dom, now.h, now.m)
print(p_coords)
