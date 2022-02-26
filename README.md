# mp-pico-solar-system

[![lint](https://github.com/alanbchristie/mp-pico-solar-system/actions/workflows/lint.yaml/badge.svg)](https://github.com/alanbchristie/mp-pico-solar-system/actions/workflows/lint.yaml)
![GitHub tag (latest SemVer)](https://img.shields.io/github/v/tag/alanbchristie/mp-pico-solar-system)
![GitHub](https://img.shields.io/github/license/alanbchristie/mp-pico-solar-system)

![Platform](https://img.shields.io/badge/platform-micropython-lightgrey)

An app designed for the **Pico Explorer Base** board and the
**RV3028** Real-Time Clock breakout. The app displays the solar system's
planets on the board's display.

![explorer](explorer.jpg)

The planets are displayed (not to scale!) on simplified circular orbits.
The orbit tracks for the four rocky inner planets are brighter,
and the orbit tracks for the outer planets are darker. **Earth** is placed on
a green orbit with (obviously) **Mars** on the nearest outer track and
**Venus** on the nearest inner track. The date of the planetary positions
is shown in the top left-hand corner of the display: -

![display](solar-system.001.png)

## Using the app
At startup the current locations of the planets are displayed

- Press (and hold) **Y** to advance the planets, one day at a time
- Press (and hold) **B** to retard the planets
- Press **X** to exit the application's main loop

## Installation
Copy the files in the `pico` directory to the root of the Raspberry Pi Pico.
`main.py` will run automatically when the explorer is switched on.
Alternatively, if you don;t want to commit `main.py` to the board you
can upload the other files and use [Thonny] to run the app.

## Credits
Planetary calculations have been taken from the code written by [Dmytro Panin]
which can be found in his [pico-solar-system] repository. I have
used his `planets.py` module, but replaced the main-loop with a version
suitable for the Pico Explorer Base.

### Mods to 3rd party code
1. `planets.py`: Added `#pylint: skip-file` to line 1
2. `main.py`: Replaced to use the RV3028 and Pico Explorer Base

---

[dmytro panin]: https://github.com/dr-mod
[pico explorer base]: https://shop.pimoroni.com/products/pico-explorer-base
[pico-solar-system]: https://github.com/dr-mod/pico-solar-system
[thonny]: https://thonny.org
