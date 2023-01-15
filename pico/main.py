"""The real-time solar-system display.

Based on code written by Dmytro Panin and enhanced
for use on the Pimoroni Explorer Base board.
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
from rtc import RTC, RealTimeClock, month_name
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
_EARTH_ORBIT: int = 2

# Initialise the Pico Explorer display,
# with a buffer using 2-bytes per pixel (240x240)
_DISPLAY_WIDTH: int = display.get_width()
_DISPLAY_HEIGHT: int = display.get_height()
_DISPLAY_BUF: bytearray = bytearray(_DISPLAY_WIDTH * _DISPLAY_HEIGHT * 2)
display.init(_DISPLAY_BUF)

# Fixed display coordinates of the Sun,
# (centre of the 240/240 display).
_SUN = (_DISPLAY_WIDTH // 2, _DISPLAY_HEIGHT // 2)

# Run the application?
# Normally True, set to False when the user
# hits the "X" button.
_RUN: bool = True

# Demo mode?
# If set the planets rotate automatically
# and the advance/retard buttons are ignored.
_DEMO: bool = False
# The demo advance limit (after which the animation begins again).
# Because we might be on a 32-bit platform, we're subject to the famous unix
# 'end-of-world' date when we advance, i.e. '2,147,483,647' seconds.
# It's the largest epoch seconds we can use without encountering an error
# (19th Jan 2038). It's 2022 now, so let's limit the DEMO advance to 10 years.
# The demo will most likely crash if used after 2028 and the while app will
# stop working altogether on a 32-but system in 16 years.
_DEMO_ADVANCE_LIMIT: int = 3_650
# Demo orbit speed
_DEMO_SPEED: int = 4

# Night mode? Everything in RED (default).
# Toggled with button "A"
_NIGHT_MODE: bool = True

# The number of days to advance the planets (from today).
# 0..n
_ADVANCE_DAYS: int = 0
# Maximum Days we're allowed to advance.
# No point in going more than a year, when earth's back to where we started.
# We're interested in the planet locations with respect to Earth,
# not interested in seeing all the planets orbit the Sun!
# After all, it takes Neptune 165 years to complete its orbit!
_ADVANCE_DAYS_MAX: int = 366
# Minimum Days we're allowed to retard.
# Zero means maximum 'retard' is now.
# A value of -180 means a maximum retard of (approximately) 6 months (from now)
_ADVANCE_DAYS_MIN: int = -366
# The number of consecutive date advance/retard operation.
# This is incremented in the 'button_press()' function
# and cleared when the button's been released (from the run() method).
# Speed is increased, based on this value.
_CONSECUTIVE_CHANGE: int = 0
# Speed threshold.
# The number of consecutive advance/retard operations that result
# in the speed doubling. Used in 'get_speed()'.
_SPEED_THRESHOLD: int = 7


def set_pen(red: int, green: int, blue: int) -> None:
    """Sets the pen colour.
    If 'night mode' only RED is passed through.
    """
    if _NIGHT_MODE:
        display.set_pen(red, 0, 0)
    else:
        display.set_pen(red, green, blue)


def get_speed() -> int:
    """Returns the advance/retard speed.
    This is based on the number of consecutive changes,
    and doubles every time the speed threshold is met.
    """
    return 2 ** (_CONSECUTIVE_CHANGE // _SPEED_THRESHOLD)


def button_pressed() -> bool:
    """Checks the buttons, acting on any supported combinations
    that are pressed.
    "Y" advances the planets.
    "B" retards the planets.
    "A" toggles night mode.
    "X" quits the app (returning to the shell)

    We return True if something's changed.
    """
    global _ADVANCE_DAYS
    global _CONSECUTIVE_CHANGE
    global _NIGHT_MODE
    global _RUN

    if display.is_pressed(display.BUTTON_X):
        _RUN = False
        return True

    if display.is_pressed(display.BUTTON_A):
        # Toggle night mode.
        _NIGHT_MODE = not _NIGHT_MODE
        # And then wait for button to be released
        # to avoid rapid toggling.
        while display.is_pressed(display.BUTTON_A):
            time.sleep_ms(100)  # type: ignore
        return True

    # If advancing, and not gone too far
    # then advance. In DEMO mode the advance/retard buttons are ignored.
    if not _DEMO and display.is_pressed(display.BUTTON_Y)\
            and _ADVANCE_DAYS < _ADVANCE_DAYS_MAX:

        # We set the 'speed' based on the number of consecutive changes,
        #
        _ADVANCE_DAYS += get_speed()
        if _ADVANCE_DAYS < _ADVANCE_DAYS_MAX:
            _CONSECUTIVE_CHANGE += 1
        else:
            _ADVANCE_DAYS = _ADVANCE_DAYS_MAX
        return True

    # If retarding, and not back too far
    # then retard. In DEMO mode the advance/retard buttons are ignored.
    if not _DEMO and display.is_pressed(display.BUTTON_B)\
            and _ADVANCE_DAYS > _ADVANCE_DAYS_MIN:
        _ADVANCE_DAYS -= get_speed()
        if _ADVANCE_DAYS > _ADVANCE_DAYS_MIN:
            _CONSECUTIVE_CHANGE += 1
        else:
            _ADVANCE_DAYS = _ADVANCE_DAYS_MIN
        return True

    if _DEMO:
        # Advance the planets in demo mode.
        # Resetting when we reach the advance limit.
        _ADVANCE_DAYS += _DEMO_SPEED
        if _ADVANCE_DAYS > _DEMO_ADVANCE_LIMIT:
            _ADVANCE_DAYS = 0

    # No change if we get here
    return False


def plot_orbit(radius: int) -> None:
    """Plots an orbit on the display.
    The pen colour is expected to have been set by the caller.
    """
    assert radius
    assert radius > 0

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


def plot_date(pt: RealTimeClock) -> None:
    """Plots the solar system date.
    """
    assert pt
    assert _ADVANCE_DAYS >= _ADVANCE_DAYS_MIN

    # The explorer text() method takes 5 arguments: -
    # - String
    # - x position
    # - y position
    # - width
    # - size

    # Plot the date in the top-left corner...
    # By using a width of '0' we force the date text onto new lines
    # at each space int it. i.e. months and years on.
    set_pen(200, 200, 200)
    month_str: str = month_name(pt.month)
    display.text(f'{pt.dom:02} {month_str} {pt.year}', 0, 0, 0, 2)

    if not _DEMO:
        # Plot 'now' if there's no advancement
        # or the number of days the display has been advanced.
        set_pen(128, 128, 128)
        if _ADVANCE_DAYS == 0:
            display.text('Now', 0, 226, 0, 2)
        else:
            # To avoid wrapping at the space between the number and 'days'
            # we need to use a width that accommodates the max offset.
            # To be safe, regardless of the offset, use the whole display width.
            prefix = '+' if _ADVANCE_DAYS > 0 else ''
            display.text(f'{prefix}{_ADVANCE_DAYS} days', 0, 226, _DISPLAY_WIDTH, 2)


def plot_system(pt: RealTimeClock) -> None:
    """This function plots the solar system for the given a RealTimeClock value
    and uses a numerical offset of days to add the date when it's not 'today'.
    """
    assert pt

    # Get planet positions (for the given date)
    p_coords = planets.coordinates(pt.year, pt.month, pt.dom, pt.h, pt.m)

    # Clear the display,
    # ready to plot the new solar system
    set_pen(0, 0, 0)
    display.clear()

    # Plot the Sun
    set_pen(230, 230, 0)
    display.circle(_SUN[0], _SUN[1], 4)

    # Plot any text first,
    # we overlay the plants on top of this so the
    # solar system is always on top.
    plot_date(pt)

    # For each planet...
    # 'orbit' runs from 0..7
    for orbit, el in enumerate(p_coords):

        # Plot its underlying (simplified) orbit
        # as a grey circle around the Sun.
        orbit_radius: int = _ORBIT_SCALE_FACTOR * (orbit + 1) + 2
        if orbit == _EARTH_ORBIT:
            # Us...
            # (bright red or green orbit)
            if _NIGHT_MODE:
                set_pen(180, 0, 0)
            else:
                set_pen(0, 150, 0)
        elif orbit < 4:
            # Rock planets...
            # (brighter orbits)
            set_pen(110, 110, 110)
        else:
            # Gas giants...
            set_pen(10, 10, 10)
        plot_orbit(orbit_radius)

        # Now plot the planet
        feta = math.atan2(el[0], el[1])
        coordinates = (orbit_radius * math.sin(feta),
                       orbit_radius * math.cos(feta))
        coordinates = (coordinates[0] + _SUN[0],
                       _DISPLAY_HEIGHT - (coordinates[1] + _SUN[1]))
        for ar in range(0, len(planets.planets_a[orbit][0]), 5):
            x = planets.planets_a[orbit][0][ar] - 50 + coordinates[0]
            y = planets.planets_a[orbit][0][ar + 1] - 50 + coordinates[1]
            if x >= 0 and y >= 0:
                if _NIGHT_MODE:
                    if orbit == _EARTH_ORBIT:
                        display.set_pen(200, 0, 0)
                    else:
                        display.set_pen(150, 0, 0)
                else:
                    display.set_pen(planets.planets_a[orbit][0][ar + 2],
                                    planets.planets_a[orbit][0][ar + 3],
                                    planets.planets_a[orbit][0][ar + 4])
                display.pixel(int(x), int(y))

    # Refresh the display
    display.update()


def run() -> None:
    """The main look, we remain here until the user
    hits the exit button.
    """
    global _CONSECUTIVE_CHANGE

    print('Running... (press and hold X to quit')

    # We update the current clock value but as the planets
    # move so slowly there's no point in continuously calling the RTC.
    # When idle we go around the loop about twice every second,
    # so we set this value to an hour, say, but start with 0
    # to force the collection of the current time on the first pass.
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
            # Reset the update countdown.
            # Idle time is 500mS, hence '2 x'
            update_countdown = 2 * _TIME_REFRESH_SECONDS
        else:
            update_countdown -= 1

        if (button_pressed() or rtc_changed or _DEMO) and _RUN:

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

            # Nothing changed, reset 'consecutive change'
            # (used for speed adjustments in the button-press)
            _CONSECUTIVE_CHANGE = 0
            # don't stress the CPU - sleep for a while.
            time.sleep_ms(500)  # type: ignore

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
