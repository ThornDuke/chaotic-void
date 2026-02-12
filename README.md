# Astronomical Planner for Scribus

An automated Python-based generator for Scribus that creates a professional, astronomical annual planner in A5 format.

## Overview

**Planner** is a script designed to run within the Scribus Python Scripter. It automates the creation of a 12-month diary (7 days spread across two pages) featuring:
* Precise **Moon Phase** calculations.
* **Sun and Planet positions** for every day of the year.
* Multi-language support.
* Automated A5 layout design.

## Requirements

The project relies on specific versions to ensure astronomical precision:

* **Scribus:** 1.6.1 or higher
* **Python:** 3.12.3
* **Libraries:**
    * `Tkinter 8.6` (UI Management)
    * [`PyEphem 4.1.5`](https://rhodesmill.org/pyephem/) (Moon phases)
    * [`SkyField 1.48`](https://rhodesmill.org/skyfield/) (Planetary calculations)
* **Fonts:**
  * `Simoncini Garamond Std` (Body text)
  * `Symbola` (Astronomical icons)
  * `AstroGadget`  (Astronomical icons)

## Installation & Usage

1.  Ensure you have Scribus installed on your system (Tested on Linux Mint 22).
2.  Clone this repository into your preferred folder.
3.  Open Scribus.
4.  Go to `Script` -> `Execute Script...` and select `Planner.py`.
5.  Choose the year and your preferred language in the pop-up form.

## Project Structure

* `Planner.py`: Main entry point.
* `src/mainform.py`: GUI for user input.
* `src/calendarist.py`: The "brain" - calculates dates and astronomical events.
* `src/designer.py`: Handles the Scribus document creation and layout.
* `src/data/`: Assets and localization files.

## License

This project is licensed under the **GNU General Public License v3.0**. See the LICENSE file for details.

---
© 2026 Sergio Spina - [sergio.am.spina@gmail.com](mailto:sergio.am.spina@gmail.com)