# -*- coding: utf-8 -*-
r"""
Planner

Scribus script for astronomical diary generation.

(C) 2026 by Sergio Spina <sergio.am.spina@gmail.com>

This script creates an annual planner based on the year and
language chosen by the user. The planner is in A5 format with
seven days spread over two pages.

USAGE

A form is displayed where you can select the reference year
and the language in which to write the texts. Once you click
"Ok," the planner is created as a Scribus file.

REQUIREMENTS

    * Scribus 1.6.1 or higher
    * Python 3.12.3
    * Tkinter 8.6
    * PyEphem 4.1.5 library for moon phases calculations <https://rhodesmill.org/pyephem/>
    * SkyField 1.48 library for the calculation of the sun and
    planets positions and for the moon eclypses <https://rhodesmill.org/skyfield/>
    * Simoncini Garamond Std font for text
    * Symbola font for moon and sun symbols
    * AstroGadget for planet symbols

When first run, Skyfield will automatically download the file
“de440s.bsp” (approximately 30MB) from a NASA server if it is
not present in the script folder.

The program was developed and tested on a Linux Mint 22 “Wilma” system.

First scratch: 2026-02-20
Discussion: <https://github.com/ThornDuke/chaotic-void/discussions>

LICENSE:

Copyright (C) 2026  Sergio Spina

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or (at your
option) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License along
with this program; if not, write to the Free Software Foundation, Inc.,
59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
"""

__program_name__ = "Planner"
__version__ = "3.2.5"
__author__ = "Thorn Duke"

import sys

try:
    import scribus  # pyright: ignore[reportMissingImports]
except ImportError:
    no_scribus_msg = (
        "\n"
        "│\n"
        f"│  {__program_name__} v. {__version__}\n"
        "│\n"
        "│  This script will only run within the\n"
        "│  Python interpreter embedded in Scribus.\n"
        "│  Try Script -> Execute Script.\n"
        "│\n"
    )
    print(no_scribus_msg)
    sys.exit(1)

import datetime
import src.mainform as mainform
import src.calendarist as calendarist
import src.designer as designer
from src.translator import translator
from src.utilities import fill, check_requirements, validate_requirements

# Translator initialization
t = translator(scribus.getGuiLanguage())


def main() -> None:
    """Main execution flow for the Planner generator."""
    sys_report = check_requirements()
    if not validate_requirements(sys_report):
        return

    # edition contains {‘observer’: str, ‘language’: str, ‘year’: int} or None
    edition = mainform.get_planner_edition()
    if edition == None:
        return

    try:
        process_start = datetime.datetime.now().replace(microsecond=0)
        year = edition["year"]
        language = edition["language"]
        observer = edition["observer"]
        # Data generation and layout creation
        calendar_data = calendarist.generate_full_calendar(year, language, observer)
        designer.create_planner_A5(calendar_data, language, observer)
        scribus.setInfo(__author__, f"Edition {year} | Observer: {observer} | Language: {language}", __program_name__)
        process_end = datetime.datetime.now().replace(microsecond=0)
        duration = process_end - process_start
        scribus.messageBox(
            t("gui.endform.title"),
            fill(t("gui.endform.outcome"), processing_time=duration),
            scribus.ICON_INFORMATION,
        )
    finally:
        if scribus.haveDoc():
            scribus.setRedraw(True)
        scribus.statusMessage("")


if __name__ == "__main__":
    main()
