# mp-pico-solar-system
An app designed for the Pico Explorer Base board and the RV3028 Real-Time Clock
breakout that displays solar system's planets on the board's display
in real-time.

## Credits
Planetary calculations have been taken from the code written by [Dmytro Panin]
which can be found in his [pico-solar-system] repository. I have
used his `planets.py` module, but the main-loop and other files are mine.

### `planets.py` (Mods)
1. Use of `# pylint: disable=import-error`

---

[dmytro panin]: https://github.com/dr-mod
[pico explorer base]: https://shop.pimoroni.com/products/pico-explorer-base
[pico-solar-system]: https://github.com/dr-mod/pico-solar-system
