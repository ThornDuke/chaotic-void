# Astronomical Planner for Scribus

An automated Python-based generator for Scribus that creates a professional, astronomical annual planner in A5 format.

## Overview

**Planner** is a script designed to run within the Scribus Python Scripter. It automates the creation of a 12-month diary (7 days spread across two pages) featuring:
* Precise **Moon Phase** calculations.
* **Sun and Planet positions** for every day of the year.
* Multi-language support.
* Automated A5 layout design.

## Requirements

This is the system on which the script was developed and tested. Upon startup, the script checks that the essential dependencies are met; if not, execution stops.

* **Linux Mint** 22.3 Cinnamon
* **Scribus:** 1.6.1
* **Python:** 3.12.3
* **Libraries:**
    * `Tkinter 8.6` (UI Management)
    * [`PyEphem 4.1.5`](https://rhodesmill.org/pyephem/) (Moon phases)
    * [`SkyField 1.48`](https://rhodesmill.org/skyfield/) (Planetary calculations)
    * [`Pytz 2026.5`](https://pypi.org/project/pytz/) (World Timezone definitions)
* **Fonts:**
  * `Simoncini Garamond Std` (Body text)
  * `Symbola` (Astronomical icons)
  * `AstroGadget`  (Astronomical icons)

## Installation & Usage

### Simplified method

1.  Ensure you have Scribus installed on your system.
2.  Clone this repository into your preferred folder.
3.  Open Scribus.
4.  Go to `Script` -> `Execute Script...` and select `Planner.py`.
5.  Choose the year and your preferred language in the pop-up form.

### Recommended Method

Scribus may sometimes fail to recognize the script directory as the current working directory (CWD), resulting in an exception. To avoid such issues, it is best to follow a more robust procedure for installing the script and its dependencies.

> [!IMPORTANT]
> This procedure applies to Linux Ubuntu/Mint.

1. After cloning the repository, open a terminal in the directory containing `Planner.py`;
2. Create the virtual environment (usually named `.venv`):
```bash
python -m venv .venv
```
3. Activate the virtual environment:
```bash
source .venv/bin/activate
```
4. Install the dependencies from the `requirements.txt` file:
```bash
pip install -r requirements.txt
```
5. Verify the installation by checking the list of packages in the environment:
```bash
pip list
```
6. Launch Scribus from the script folder so that the scripter can locate the dependencies within the virtual environment:
```bash
scribus -ns --
```
7. You can now open the script in Scribus. Navigate to the `Script` menu -> `Execute Script...`, then locate and select `Planner.py`.
8. In the form that appears, select the year, the text language, and the observer's location.

## Project Structure

* `Planner.py`: Main entry point.
* `src/mainform.py`: GUI for user input.
* `src/calendarist.py`: The "brain" - calculates dates and astronomical events.
* `src/designer.py`: Handles the Scribus document creation and layout.
* `src/data/`: Assets and localization files.
* `intl/*.json`: Internationalization files.

## License

This project is licensed under the **GNU General Public License v3.0**. See the LICENSE file for details.

---
© 2026 Sergio Spina - [sergio.am.spina@gmail.com](mailto:sergio.am.spina@gmail.com)