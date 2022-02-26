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
# Used to refresh the current time in the main loop.
_TIME_REFRESH_SECONDS: int = 3_600

# The orbit radius?
# Adjust to fit the screen,
# 14 is good for the Pico Explorer Base
_ORBIT_SCALE_FACTOR: int = 14

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

# Run the application?
# Normally True, set to False when the user
# hits the "X" button.
_RUN: bool = True

# The number of days to advance the planets (from today).
# 0..n
_ADVANCE_DAYS: int = 0
# Maximum Days we're allowed to advance. 4 Years?
_ADVANCE_DAYS_MAX: int = 1461


def button_pressed() -> bool:
    """Checks the buttons, acting on any supported combinations
    that are pressed. Y advances the planets, B retards them and
    is an exit command.

    We return True if something's changed.
    """
    global _ADVANCE_DAYS
    global _RUN

    if display.is_pressed(display.BUTTON_X):
        _RUN = False
        return True
    elif display.is_pressed(display.BUTTON_Y)\
            and _ADVANCE_DAYS < _ADVANCE_DAYS_MAX:
        _ADVANCE_DAYS += 1
        return True
    elif display.is_pressed(display.BUTTON_B)\
            and _ADVANCE_DAYS > 0:
        _ADVANCE_DAYS -= 1
        return True

    # No change if we get here
    return False


def plot_orbit(radius: int) -> None:
    """Plots an orbit on the display.
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
    # 'orbit' runs from 0..7
    for orbit, el in enumerate(p_coords):

        # Plot its underlying (simplified) orbit
        # as a grey circle around the Sun.
        orbit_radius: int = _ORBIT_SCALE_FACTOR * (orbit + 1) + 2
        if orbit == 2:
            # Us...
            # (bright green orbit)
            display.set_pen(0, 150, 0)
        elif orbit < 4:
            # Rock planets...
            # (brighter orbits)
            display.set_pen(110, 110, 110)
        else:
            # Gas giants...
            display.set_pen(10, 10, 10)
        plot_orbit(orbit_radius)

        # Now plot the planet
        feta = math.atan2(el[0], el[1])
        coordinates = (orbit_radius * math.sin(feta),
                       orbit_radius * math.cos(feta))
        coordinates = (coordinates[0] + _SUN[0],
                       _HEIGHT - (coordinates[1] + _SUN[1]))
        for ar in range(0, len(planets.planets_a[orbit][0]), 5):
            x = planets.planets_a[orbit][0][ar] - 50 + coordinates[0]
            y = planets.planets_a[orbit][0][ar + 1] - 50 + coordinates[1]
            if x >= 0 and y >= 0:
                display.set_pen(planets.planets_a[orbit][0][ar + 2],
                                planets.planets_a[orbit][0][ar + 3],
                                planets.planets_a[orbit][0][ar + 4])
                display.pixel(int(x), int(y))

    # Plot the date in the top-left corner...
    display.set_pen(255, 255, 255)
    display.text(f'{pt.dom:02}', 0, 0, 0, 2)
    display.text(_MONTH[pt.month], 0, 15, 0, 2)
    display.text(f'{pt.year % 100}', 0, 30, 0, 2)

    # Refresh the display
    display.update()


def run() -> None:
    """The main look, we remain here until the user
    hits the exit button."""

    print('Running... (press and hold X to quit')

    # When do we update the current clock?
    # When idle we go around the loop about 1 every second,
    # so we set this to _TIME_REFRESH_SECONDS but start with 0
    # to force the collection of the current time.
    update_countdown: int = 0
    while _RUN:

        # Update the current time?
        rtc_changed: bool = False
        if update_countdown == 0:
            print('Getting new time of day...')
            # What time is it now?
            now: RealTimeClock = _RTC.datetime()
            now_seconds: float = time.mktime((now.year,
                                              now.month,
                                              now.dom,
                                              now.h,
                                              0, 0, 0, 0, 0))
            print(f'Got {now}')
            rtc_changed = True
            # Reset the update timer
            update_countdown = _TIME_REFRESH_SECONDS
        else:
            update_countdown -= 1

        if (button_pressed() or rtc_changed) and _RUN:

            # Add any daily offset to the current time (epoch seconds)
            plot_seconds = now_seconds + _ADVANCE_DAYS * _DAY_SECONDS
            # Use a gmtime() to get the required UTC date
            gm_time: Tuple = time.gmtime(plot_seconds)
            # Convert to our RTC named-tuple.
            # We don't care about day-of-week, minute or second
            rtc: RealTimeClock = RealTimeClock(gm_time[0], gm_time[1],
                                               gm_time[2],
                                               0, gm_time[3], 0, 0)
            # Display the solar system
            plot_system(rtc)

        else:

            # Nothing changed,
            # don't stress the CPU - sleep for a while.
            time.sleep(1)

    print('Done, bye')

    # Wipe the display on the way out
    display.set_pen(0, 0, 0)
    display.clear()
    display.update()
    

# MAIN ------------------------------------------------------------------------

if __name__ == '__main__':

    # If running enter the 'main loop'...
    if _RUN:
        run()
