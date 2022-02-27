"""A simplified micropython-style real-time clock.
A wrapper around the RV3028 I2C module.
"""
import time
try:
    from typing import Optional
except ImportError:
    pass

# pylint: disable=import-error
from pimoroni_i2c import PimoroniI2C  # type: ignore
from breakout_rtc import BreakoutRTC  # type: ignore
from ucollections import namedtuple  # type: ignore

# A Real-Time Clock value
# Year is full year, e.g. 2022
RealTimeClock: namedtuple =\
    namedtuple('RealTimeCLock',
               ('year', 'month', 'dom', 'dow', 'h', 'm', 's'))


# Short text representation of the month
# (1-based, i.e. Jan == 1)
_MONTH_NAME = ["---",
               "Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def month_name(month: int) -> str:
    """Returns the short name of the Month.
    """
    assert 0 < month <= 12

    return _MONTH_NAME[month]


class RTC:
    """A wrapper around the Pimoroni BreakoutRTC class,
    a driver for the RV3028 RTC I2C breakout module.
    """

    def __init__(self, sda: int, scl: int):
        """Initialises the object.
        """
        # Create an object from the expected (built-in) Pimoroni library
        # that gives us access to the RV3028 RTC. We use this
        # to set the value after editing.
        self._pimoroni_i2c: PimoroniI2C = PimoroniI2C(sda=sda, scl=scl)
        self._rtc: BreakoutRTC = BreakoutRTC(self._pimoroni_i2c)
        # Setting backup switchover mode to '3'
        # means the device will switch to battery
        # when the power supply drops out.
        self._rtc.set_backup_switchover_mode(3)
        # And set to 24 hour mode (essential)
        self._rtc.set_24_hour()

    def datetime(self, new_datetime: Optional[RealTimeClock] = None)\
            -> RealTimeClock:
        """Gets (or sets and returns) the real-time clock.
        """
        if new_datetime is not None:
            # Given a date-time,
            # so use it to set the RTC value.
            #
            # We use a 1-based day of the week,
            # the underlying RTC uses 0-based.
            assert new_datetime.dow > 0
            self._rtc.set_time(new_datetime.s, new_datetime.m, new_datetime.h,
                               new_datetime.dow - 1,
                               new_datetime.dom,
                               new_datetime.month,
                               new_datetime.year)

        # Get the current RTC value,
        # waiting until a value is ready.
        new_rtc: Optional[RealTimeClock] = None
        while new_rtc is None:
            if self._rtc.update_time():
                new_rtc = RealTimeClock(
                    self._rtc.get_year(),
                    self._rtc.get_month(),
                    self._rtc.get_date(),
                    self._rtc.get_weekday() + 1,
                    self._rtc.get_hours(),
                    self._rtc.get_minutes(),
                    self._rtc.get_seconds())
            else:
                # No time available,
                # sleep for a very short period (less than a second)
                time.sleep_ms(250)  # type: ignore

        return new_rtc
