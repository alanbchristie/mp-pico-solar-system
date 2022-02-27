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

As you hold **X** or **B** the speed that the planets advance or retard
increases, i.e. they orbit faster the longer you press the buttons.

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

**Anatomy of `planets.py`**

The `planets.py` module is unchanged from Dmytro's original. Unfortunately
it has no documentation, and I've reverse-engineered some potentially
helpful documentation here...

- `planets_a` is a list of planet 'bitmaps' (spriies). The array has
  eight entries, one for each planet (Mercury to Neptune). Each array
  entry is a one-dimensional list of numbers but is 'interpreted' as
  consecutive blocks (rows) of 5-byte values for each pixel in the bitmap.
  The five bytes are the pixel's 'x', 'y', 'red', 'green', and 'blue' value.
  The bitmap size is 7x7 with 'x' and 'y' values ranging from 47 to 50.
  The pixel at 50,50 (the centre of the bitmap) is placed on planet's
  _coordinate_.

---

[dmytro panin]: https://github.com/dr-mod
[pico explorer base]: https://shop.pimoroni.com/products/pico-explorer-base
[pico-solar-system]: https://github.com/dr-mod/pico-solar-system
[thonny]: https://thonny.org
