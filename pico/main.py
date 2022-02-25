"""The real-time solar-system display.

https://github.com/pimoroni/pimoroni-pico/tree/main/micropython/examples/pico_explorer
"""
import math
import time
try:
    from typing import List, Optional, Tuple
except ImportError:
    pass

# pylint: disable=import-error
import micropython  # type: ignore
from machine import I2C, Pin  # type: ignore
import picoexplorer as display  # type: ignore

# Application modules
from rtc import RTC, RealTimeClock
import planets

# Uncomment when debugging callback problems
micropython.alloc_emergency_exception_buf(100)

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
# Seconds in a day
_DAY_SECONDS: int = 86_400

# Initialise the Pico Explorer display,
# with a buffer using 2-bytes per pixel (240x240)
_WIDTH: int = display.get_width()
_HEIGHT: int = display.get_height()
_BUF: bytearray = bytearray(_WIDTH * _HEIGHT * 2)
display.init(_BUF)

# Fixed display coordinates of the Sun,
# (centre of the 240/240 display).
_SUN = (_WIDTH // 2, _HEIGHT // 2)

# Short text representation of the month
# (1-based, i.e. Jan == 1)
_MONTH = ["---",
          "Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def plot_orbit(radius):
    """Plots an orbit on the diisplay.
    The pen colour is expected to have been set by the caller.
    """
    # Centre of the orbit...
    cx: int = _SUN[0]
    cy: int = _SUN[1]
    x: int = radius - 1
    y: int = 0
    dx: int = 1
    dy: int = 1
    err: int = dx - (radius << 1)
    while x >= y:
        display.pixel(cx + x, cy + y)
        display.pixel(cx + y, cy + x)
        display.pixel(cx - y, cy + x)
        display.pixel(cx - x, cy + y)
        display.pixel(cx - x, cy - y)
        display.pixel(cx - y, cy - x)
        display.pixel(cx + y, cy - x)
        display.pixel(cx + x, cy - y)
        if err <= 0:
            y += 1
            err += dy
            dy += 2
        if err > 0:
            x -= 1
            dx += 2
            err += dx - (radius << 1)


def plot_system(pt: RealTimeClock):
    """This function plots the solar system for the given a RealTimeClock value
    and uses a numerical offset of days to add the date when it's not 'today'.
    """

    # Get planet positions (for the given date)
    p_coords = planets.coordinates(pt.year, pt.month, pt.dom, pt.h, pt.m)

    # Clear the display,
    # ready to plot the new solar system
    display.set_pen(0, 0, 0)
    display.clear()

    # Plot the Sun
    display.set_pen(255, 255, 0)
    display.circle(_SUN[0], _SUN[1], 4)

    # For each planet...
    for i, el in enumerate(p_coords):
        # Plot its underlying (simplified) orbit
        # as a grey circle around the Sun,
        # scaling so it fits the pico display
        orbit_radius: int = 14 * (i + 1) + 2
        if i == 2:
            # Us...
            # (bright green orbit)
            display.set_pen(0, 150, 0)
        elif i < 4:
            # Rock planets...
            # (brighter orbits)
            display.set_pen(110, 110, 110)
        else:
            # Gas giants...
            display.set_pen(10, 10, 10)
        plot_orbit(orbit_radius)
        # Now plot the planets
        feta = math.atan2(el[0], el[1])
        coordinates = (orbit_radius * math.sin(feta), orbit_radius * math.cos(feta))
        coordinates = (coordinates[0] + _SUN[0], _HEIGHT - (coordinates[1] + _SUN[1]))
        for ar in range(0, len(planets.planets_a[i][0]), 5):
            x = planets.planets_a[i][0][ar] - 50 + coordinates[0]
            y = planets.planets_a[i][0][ar + 1] - 50 + coordinates[1]
            if x >= 0 and y >= 0:
                display.set_pen(planets.planets_a[i][0][ar + 2],
                                planets.planets_a[i][0][ar + 3],
                                planets.planets_a[i][0][ar + 4])
                display.pixel(int(x), int(y))

    display.set_pen(255, 255, 255)
    display.text(f'{pt.dom:02}', 0, 0, 0, 2)
    display.text(_MONTH[pt.month], 0, 15, 0, 2)
    display.text(f'{pt.year % 100}', 0, 30, 0, 2)

    # Update the display
    display.update()

# What time is it now?
_NOW: RealTimeClock = _RTC.datetime()

# Move planets one day at a time for a year.
#
# Calculating the planet's positions slows the display refresh
# so we don't need to pause between screens.
# Use mktime/gmtime to conveniently calculate new future dates
# (we don't care about minutes, seconds, day-of-week or day-of-year).
_PT_SECONDS: float = time.mktime((_NOW.year, _NOW.month, _NOW.dom, _NOW.h,
                                  0, 0, 0, 0, 0))
for _ in range(365):
    # Calculate today's time (epoch seconds)
    _PT_SECONDS += _DAY_SECONDS
    # Get a gmtime (UTC) from epoch seconds
    gm_time: Tuple = time.gmtime(_PT_SECONDS)
    # Convert to our RTC
    # Don't care about day-of-week, minute or second)
    rtc: RealTimeClock = RealTimeClock(gm_time[0], gm_time[1], gm_time[2],
                                       0, gm_time[3], 0, 0)
    # Display the solar system
    plot_system(rtc)
