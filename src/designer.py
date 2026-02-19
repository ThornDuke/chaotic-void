# -*- coding: utf-8 -*-
"""
Planner Layout Designer Module.
This module handles the visual generation of the planner within Scribus,
managing page creation, drawing lines, and placing text frames for
dates, holidays, astronomical data, and seasons.
"""

import sys
import datetime
import re
import scribus  # pyright: ignore[reportMissingImports]
from .data.lines import get_A5_line_data
from .translator import translator, by_acronym
from .utilities import (
    fill,
    round_dt_to_min,
    generate_filename,
    save_to_file,
)
from . import constants

# --temp / debug
# from src.archivist import Logger
# --remove before release--/

ui_t = translator(by_acronym(scribus.getGuiLanguage()))


def hour_min(dt):
    """
    Convert various datetime-like inputs into a standardized HH:MM string.

    Args:
        dt (Union[datetime.time, datetime.datetime, str, None]): The time or
            date object/string to be formatted.

    Returns:
        str: The formatted time as "HH:MM", or the original input if
            parsing fails.
    """
    if dt is None or dt == "":
        return ""

    if isinstance(dt, datetime.time):
        return dt.strftime("%H:%M")

    if isinstance(dt, datetime.datetime):
        return round_dt_to_min(dt).time().strftime("%H:%M")

    if isinstance(dt, str):
        # Try parsing common time formats first
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                t = datetime.datetime.strptime(dt, fmt).time()
                return t.strftime("%H:%M")
            except Exception:
                pass

        # Try ISO datetime
        try:
            dt_obj = datetime.datetime.fromisoformat(dt)
            return round_dt_to_min(dt_obj).time().strftime("%H:%M")
        except Exception:
            pass

        # Fallback: extract first occurrence of HH:MM
        m = re.search(r"(\d{1,2}):(\d{2})", dt)
        if m:
            hh = int(m.group(1))
            mm = int(m.group(2))
            return f"{hh:02d}:{mm:02d}"

        # If nothing matches, return the original string
        return dt


def create_A5_document():
    """Creates a new Scribus document with A5 dimensions and specific margins."""
    scribus.newDocument(
        scribus.PAPER_A5_MM,
        (10, 17, 10, 10),  # Margins: Top, Left, Bottom, Right
        scribus.PORTRAIT,
        1,
        scribus.UNIT_MM,
        scribus.FACINGPAGES,
        0,
        1,
    )


def createLineStyles():
    """
    Initialize custom line styles (thin and thick) within the Scribus document.
    """
    scribus.createCustomLineStyle("thin", [{"Color": "Black", "Width": 0.33}])
    scribus.createCustomLineStyle("thick", [{"Color": "Black", "Width": 1}])


def createTextStyles():
    """
    Define and create all necessary Character and Paragraph styles in Scribus.

    Sets up typography for titles, headers, weekdays, moon phases,
    and ephemeris symbols using specific font families and sizes.
    """
    scribus.createCharStyle(
        name="title_ch_style", font="Simoncini Garamond Std Roman", fontsize=34
    )
    scribus.createCharStyle(
        name="header_ch_style", font="Simoncini Garamond Std Roman", fontsize=21
    )
    scribus.createCharStyle(
        name="weekday_ch_style", font="Simoncini Garamond Std Bold", fontsize=8.30
    )
    scribus.createCharStyle(
        name="text_ch_style", font="Simoncini Garamond Std Roman", fontsize=8.30
    )
    scribus.createCharStyle(
        name="moonphase_ch_style", font="Symbola Regular", fontsize=8.30
    )
    scribus.createCharStyle(
        name="ephem_sym_ch_style", font="AstroGadget Regular", fontsize=8.30
    )
    scribus.createCharStyle(
        name="smallcaps_ch_style",
        font="Simoncini Garamond Std Roman",
        fontsize=8.30,
        features="smallcaps",
    )
    scribus.createCharStyle(
        name="bold_ch_style", font="Simoncini Garamond Std Bold", fontsize=8.30
    )
    scribus.createCharStyle(
        name="bold10_ch_style", font="Simoncini Garamond Std Bold", fontsize=10
    )
    scribus.createCharStyle(
        name="smallcaps10_ch_style",
        font="Simoncini Garamond Std Roman",
        fontsize=10,
        features="smallcaps",
    )
    scribus.createCharStyle(
        name="text10_ch_style", font="Simoncini Garamond Std Roman", fontsize=10
    )

    scribus.createParagraphStyle(
        "title_par_style", 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, "title_ch_style"
    )
    scribus.createParagraphStyle(
        "header_left_par_style", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "header_ch_style"
    )
    scribus.createParagraphStyle(
        "header_right_par_style", 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, "header_ch_style"
    )
    scribus.createParagraphStyle(
        "weekday_par_style", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "weekday_ch_style"
    )
    scribus.createParagraphStyle(
        "text_left_par_style", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "text_ch_style"
    )
    scribus.createParagraphStyle(
        "text_right_par_style", 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, "text_ch_style"
    )
    scribus.createParagraphStyle(
        "title_explanation_par_style", 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, "text_ch_style"
    )
    scribus.createParagraphStyle(
        "text_smallcaps_par_style",
        0,
        10,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "smallcaps_ch_style",
    )
    scribus.createParagraphStyle(
        "text_bold_par_style", 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, "bold_ch_style"
    )
    scribus.createParagraphStyle(
        "planets_bold_par_style", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "bold10_ch_style"
    )
    scribus.createParagraphStyle(
        "planets_smallcaps_par_style",
        1,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        "smallcaps10_ch_style",
    )
    scribus.createParagraphStyle(
        "planets_left_par_style", 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, "text10_ch_style"
    )
    scribus.createParagraphStyle(
        "planets_events_par_style", 0, 14.25, 0, 0, 0, 0, 0, 0, 0, 0, 0, "text_ch_style"
    )


def draw_lines(side):
    """
    Draws the background grid lines for a page.

    Args:
      side (str): 'left' or 'right' to determine line coordinates and specific vertical lines.
    """
    line_data = get_A5_line_data(side)
    for data in line_data:
        line = scribus.createLine(
            data["x"], data["y"], data["x"] + data["w"], data["y"]
        )
        scribus.setCustomLineStyle("thick" if data["th"] == 1 else "thin", line)

    if side == "right":
        # Additional vertical separator for the right page (weekend section)
        vline = scribus.createLine(77.5, 139.361, 77.5, 139.361 + 60.639)
        scribus.setCustomLineStyle("thin", vline)


def split_list(input_list):
    """
    Splits the list of days into chunks of 4 and 3 to fit facing pages.
    Left pages usually take 3 days, right pages take 4 (including the weekend split).

    Args:
      input_list (list): The complete list of days.

    Returns:
      list[list]: A list of chunks (alternating sizes 3 and 4).
    """
    result = []
    i = 0
    is_three = False  # Starts with a group of 4

    while i < len(input_list):
        if is_three:
            result.append(input_list[i : i + 3])
            i += 3
        else:
            result.append(input_list[i : i + 4])
            i += 4
        is_three = not is_three

    return result


def resize_height(frame):
    w, _ = scribus.getSize(frame)
    currh = 190
    step = 1
    while True:
        scribus.sizeObject(w, currh, frame)
        if (scribus.textOverflows(frame, 1) > 0) or (currh == 0):
            break
        currh -= step
    currh += step
    scribus.sizeObject(w, currh, frame)
    return currh


def resize_width(frame):
    _, h = scribus.getSize(frame)
    currw = 120
    step = 1
    while True:
        scribus.sizeObject(currw, h, frame)
        if (scribus.textOverflows(frame, 1) > 0) or (currw == 0):
            break
        currw -= step
    currw += step
    scribus.sizeObject(currw, h, frame)
    return currw


def draw_weekday_frame(x, y, w, h, text):
    """Creates a text frame for the weekday name and day number."""
    text_frame = scribus.createText(x, y, w, h)
    scribus.setText(text, text_frame)
    scribus.setParagraphStyle("weekday_par_style", text_frame)


def draw_holyday_frame(x, y, w, h, text):
    """Creates a text frame for holiday names."""
    text_frame = scribus.createText(x, y, w, h)
    scribus.setText(text, text_frame)
    scribus.setParagraphStyle("text_left_par_style", text_frame)


def draw_season_frame(x, y, w, h, text):
    """Creates a text frame for seasons (Equinoxes/Solstices)."""
    text_frame = scribus.createText(x, y, w, h)
    scribus.setText(text, text_frame)
    scribus.setParagraphStyle("text_right_par_style", text_frame)


def draw_moon_phases_frame(x, y, w, h, moon_phase, phase_time):
    """
    Creates a text frame with lunar symbols and times.
    Uses the 'Symbola' font for correctly rendering astronomical glyphs.
    """
    if moon_phase == "":
        return

    text_frame = scribus.createText(x, y, w, h)
    moon_symbols = {
        "new": "🌑",
        "firstquarter": "🌓",
        "full": "🌕",
        "lastquarter": "🌗",
    }
    moon_symbol = moon_symbols.get(moon_phase, "")
    text = f"{moon_symbol}  {hour_min(phase_time)}"

    scribus.setText(text, text_frame)
    scribus.setParagraphStyle("text_right_par_style", text_frame)

    # Format symbols with specialized font
    moon_index = text.find(moon_symbol)
    scribus.selectText(moon_index + 1, 1, text_frame)
    scribus.setCharacterStyle("moonphase_ch_style")


def draw_planets_ephemeris(x_pos, y_pos, datadict):
    """
    Draws the ephemeris table for planets (symbol + rise/transit/set times)
    at the specified coordinates in a Scribus document.

    This function iterates through a standard list of planets, creates a text
    frame for the planet's symbol (using 'AstroGadget Regular' font) and a text frame
    for the ephemeris data (using 'Simoncini Garamond').

    Args:
      x_pos (float): The horizontal starting position (X coordinate).
      y_pos (float): The vertical starting position (Y coordinate).
      datadict (dict): A dictionary containing planetary data.
                       Expected keys follow the pattern:
                       - '{planet}_rise' (str)
                       - '{planet}_transit' (str)
                       - '{planet}_set' (str)
                       - '{planet}_isvisible' (bool)
                       Where {planet} is one of: sun, moon, mercury, venus,
                       mars, jupiter, saturn.

    Returns:
      None
    """
    y_gap = 4.983

    # Ordered list of planets to process
    planets = [
        ("sun", "A"),
        ("moon", "B"),
        ("mercury", "C"),
        ("venus", "D"),
        ("mars", "E"),
        ("jupiter", "F"),
        ("saturn", "G"),
        ("uranus", "H"),
        ("neptune", "I"),
    ]

    # vengono stampati solo quelli che hanno un campo '<planet>_set'
    filtered_planets = list(filter(lambda item: f"{item[0]}_set" in datadict, planets))

    # --- 1. Draw planets Frame ---
    for i, (planet, sym) in enumerate(reversed(filtered_planets)):
        current_y = y_pos - (y_gap * i)
        ephem_text = f"{sym}"
        # specific keys retrieval
        p_rise = datadict.get(f"{planet}_rise", "")
        p_rise_time = hour_min(p_rise) if p_rise != "" else ""
        p_transit = datadict.get(f"{planet}_transit", "")
        p_transit_time = hour_min(p_transit) if p_transit != "" else ""
        p_set = datadict.get(f"{planet}_set", "")
        p_set_time = hour_min(p_set) if p_set != "" else ""
        ephem_text = f"{sym}  {p_rise_time}  {p_transit_time}  {p_set_time}"
        ephem_frame = scribus.createText(x_pos, current_y, 30, 3)
        scribus.setText(ephem_text, ephem_frame)
        scribus.setParagraphStyle("text_right_par_style", ephem_frame)
        scribus.selectText(0, 1, ephem_frame)
        scribus.setCharacterStyle("ephem_sym_ch_style")


def draw_planet_events(x_pos, y_pos, str):
    def chunk_idxs(curr_str):
        results = []
        current_offset = 0

        lines = curr_str.splitlines(keepends=True)

        for line in lines:
            first_space = line.find(" ")
            if first_space != -1:
                start_pos = current_offset + first_space + 1

                h_idx = line.find("h")
                if h_idx != -1:
                    space_before_h = line[:h_idx].rfind(" ")
                    length = space_before_h - first_space - 1
                    results.append((start_pos, length))

            current_offset += len(line)

        return results

    if len(str) > 0:
        # crea il frame di testo
        text_frame = scribus.createText(x_pos, y_pos, 29, 100)
        scribus.setText(str, text_frame)
        scribus.setParagraphStyle("planets_events_par_style", text_frame)
        scribus.setTextVerticalAlignment(scribus.ALIGNV_BOTTOM, text_frame)
        # aggiunge la formattazione per carattere
        idxs = chunk_idxs(str)
        for start, length in idxs:
            scribus.selectText(start - 2, 1, text_frame)
            scribus.setCharacterStyle("ephem_sym_ch_style")
            scribus.selectText(start, length, text_frame)
            scribus.setCharacterStyle("smallcaps_ch_style")
        # ottimizza le dimensioni e lo posiziona con precisione
        frame_height = resize_height(text_frame)
        scribus.moveObjectAbs(x_pos, y_pos - frame_height - 0.365, text_frame)


def draw_page(side, items):
    """
    Render a complete document page layout including headers and daily data.

    Calculates coordinates and places text frames for month, year, moon phases,
    holidays, and ephemeris. Adjusts layout dynamically based on whether the
    page is a left-hand or right-hand side.

    Args:
        side (str): The page orientation, either 'left' or 'right'.
        items (list[dict]): A list of data dictionaries containing daily
            information (month, year, day, weekday, phase, holiday, etc.).
    """

    def generate_events_str(dct):
        planets = [
            ("mercury", "C"),
            ("venus", "D"),
            ("moon", "B"),
            ("mars", "E"),
            ("jupiter", "F"),
            ("saturn", "G"),
            ("uranus", "H"),
            ("neptune", "I"),
        ]
        conj_types = {"o": "opp", "c": "conj", "sc": "sup conj", "ic": "inf conj"}
        eclipse_types = {
            0: "pen",
            1: "part",
            2: "tot",
        }
        strings = []

        for planet, sym in planets:
            if f"{planet}_elong_time" in dct:
                event_sign = (
                    "mee" if dct[f"{planet}_elong_direction"] == "east" else "mew"
                )
                event_time = hour_min(dct[f"{planet}_elong_time"])
                strings.append(f"{sym} {event_sign} h{event_time}")
            if f"{planet}_oc" in dct:
                event_sign = conj_types[dct[f"{planet}_oc_type"]]
                event_time = hour_min(dct[f"{planet}_oc_time"])
                strings.append(f"{sym} {event_sign} h{event_time}")
            if f"{planet}_eclipse_time" in dct:
                event_sign = f"ecl {eclipse_types[dct[f"{planet}_eclipse_type_num"]]}"
                event_time = hour_min(dct[f"{planet}_eclipse_time"])
                strings.append(f"{sym} {event_sign} h{event_time}")

        return "\n".join(strings)

    year_string = str(items[0]["year"])
    month_string = items[0]["translated_month"]

    # Month header
    month_frame = scribus.createText(10 if side == "left" else 88.152, 10, 49.848, 8)
    scribus.setText(month_string, month_frame)
    scribus.setParagraphStyle(f"header_{side}_par_style", month_frame)

    # Year header
    year_frame = scribus.createText(104.781 if side == "left" else 17, 10, 26.219, 8)
    scribus.setText(year_string, year_frame)
    scribus.setParagraphStyle(
        f"header_{'right' if side == 'left' else 'left'}_par_style", year_frame
    )

    draw_lines(side)

    for i in range(3):
        y_offset = 19.521 + (i * 60.562)
        # weekday frames
        draw_weekday_frame(
            10 if side == "left" else 17,
            y_offset,
            60,
            3.5,
            f"{items[i]['translated_weekday']} {items[i]['day']}",
        )

        # Moon data
        # Special coordinates for the third day (sharing row with the fourth)
        if side == "right":
            sun_x = 17.575 if i == 2 else 78
            draw_moon_phases_frame(
                sun_x,
                y_offset,
                60,
                3.5,
                f"{items[i].get('phase', '')}",
                items[i].get("phase_time", ""),
            )
        else:
            draw_moon_phases_frame(
                71,
                y_offset,
                60,
                3.5,
                f"{items[i].get('phase', '')}",
                items[i].get("phase_time", ""),
            )

        # holidays
        if "holiday_name" in items[i]:
            draw_holyday_frame(
                10 if side == "left" else 17,
                y_offset + 5.073,
                60,
                3.5,
                items[i]["holiday_name"],
            )

        # Season
        if "season" in items[i]:
            if side == "right":
                season_x = 17.575 if i == 2 else 78
                draw_season_frame(
                    season_x, y_offset + 5.073, 60, 3.5, items[i]["season"]
                )
            else:
                draw_season_frame(71, y_offset + 5.073, 60, 3.5, items[i]["season"])

        # Planets Ephemeris
        if side == "left":
            draw_planets_ephemeris(101, 75.362 + (i * 60.537), items[i])

        # Planets Events
        if side == "left":
            draw_planet_events(10, 78.726 + (i * 60.537), generate_events_str(items[i]))

    if side == "right":  # out of the cicle because draw a full page
        draw_planets_ephemeris(108, 75.362, items[0])
        draw_planets_ephemeris(108, 135.899, items[1])
        draw_planets_ephemeris(47.324, 196.436, items[2])
        draw_planets_ephemeris(108, 196.436, items[3])
        draw_planet_events(17, 78.726, generate_events_str(items[0]))
        draw_planet_events(17, 139.276, generate_events_str(items[1]))
        draw_planet_events(17, 199.825, generate_events_str(items[2]))
        draw_planet_events(77.676, 199.825, generate_events_str(items[3]))

    # Handle the 4th day specifically (left column of the last row)
    if side == "right":
        draw_weekday_frame(
            77.425,
            140.637,
            60,
            3.5,
            f"{items[3]['translated_weekday']} {items[3]['day']}",
        )
        draw_moon_phases_frame(
            78,
            140.637,
            60,
            3.5,
            f"{items[3]['phase'] if 'phase' in items[3] else ''}",
            f"{hour_min(items[3]['phase_time']) if 'phase_time' in items[3] else ''}",
        )
        if "holiday_name" in items[3]:
            draw_holyday_frame(77.725, 145.710, 60, 3.5, items[3]["holiday_name"])
        if "season" in items[3]:
            draw_season_frame(78, 145.710, 60, 3.5, items[3]["season"])


def get_main_year(data):
    """Finds the primary year by looking for February 1st."""
    first_day = next(
        (item for item in data if item["month"] == 2 and item["day"] == 1), None
    )
    return first_day["year"] if first_day else None


def extract_planetary_events(input_data):
    # Struttura di base del risultato
    result = {
        "easter": "",
        "seasons": [],
        "mercury": [],
        "venus": [],
        "moon": [],
        "mars": [],
        "jupiter": [],
        "saturn": [],
        "uranus": [],
        "neptune": [],
    }

    for entry in input_data:
        # --- PASQUA ---
        if "is_easter" in entry:
            m = str(entry["month"]).zfill(2)
            d = str(entry["day"]).zfill(2)
            full_date_str = f"{entry['year']}-{m}-{d}"
            result["easter"] = full_date_str

        # --- EQUINOZI ---
        if "season" in entry:
            m = str(entry["month"]).zfill(2)
            d = str(entry["day"]).zfill(2)
            full_date_str = f"{entry['year']}-{m}-{d}"
            result["seasons"].append(
                {"date": full_date_str, "event": entry["season_type"]}
            )

        # --- PIANETI INTERNI ---
        for ip in ["mercury", "venus"]:
            # Congiunzioni
            if f"{ip}_oc_type" in entry:
                event = "INF_CONJ" if entry[f"{ip}_oc_type"] == "ic" else "SUP_CONJ"
                result[ip].append({"date": entry[f"{ip}_oc_time"], "event": event})

            # Elongazioni massime
            if f"{ip}_elong_direction" in entry:
                event = "MEE" if entry[f"{ip}_elong_direction"] == "east" else "MEW"
                result[ip].append(
                    {
                        "date": entry[f"{ip}_elong_time"],
                        "event": event,
                        "degree": entry[f"{ip}_elong_degrees"],
                    }
                )

        # --- LUNA (Eclissi) ---
        if any(item.startswith("moon_eclipse_") for item in entry):
            m = str(entry["month"]).zfill(2)
            d = str(entry["day"]).zfill(2)
            full_date_str = f"{entry['year']}-{m}-{d} {entry['moon_eclipse_time']}"
            result["moon"].append(
                {
                    "date": full_date_str,
                    "event": "MOON_ECL",
                    "type": entry["moon_eclipse_type_num"],
                }
            )

        # --- PIANETI ESTERNI ---
        # Congiunzioni
        for ep in ["mars", "jupiter", "saturn", "uranus", "neptune"]:
            if f"{ep}_oc_type" in entry:
                event = "CONJ" if entry[f"{ep}_oc_type"] == "c" else "OPP"
                result[ep].append({"date": entry[f"{ep}_oc_time"], "event": event})

    return result


def drawFirstPage(data, language):
    def _draw_planet_frame(ypos, text):
        text_frame = scribus.createText(
            17, ypos, 60 if not text.startswith("<") else 120, 3.5
        )
        scribus.setText(text, text_frame)
        scribus.setParagraphStyle("text_left_par_style", text_frame)
        scribus.selectText(0, 1, text_frame)
        scribus.setCharacterStyle("ephem_sym_ch_style")

    def _draw_acronym_frame(ypos, text, small_text):
        text_frame = scribus.createText(78, ypos, 60, 3.5)
        scribus.setText(text, text_frame)
        scribus.setParagraphStyle("text_left_par_style", text_frame)
        scribus.selectText(0, len(small_text), text_frame)
        scribus.setCharacterStyle("smallcaps_ch_style")

    t = translator(language)
    year = get_main_year(data)

    title_frame = scribus.createText(17, 80.213, 121, 12.803)
    scribus.setText(f"{year}", title_frame)
    scribus.setParagraphStyle("title_par_style", title_frame)

    legend_frame = scribus.createText(17, 136.240, 121, 3.5)
    scribus.setText(f"{t('legend')}", legend_frame)
    scribus.setParagraphStyle("text_left_par_style", legend_frame)

    moonphases_frame = scribus.createText(17, 140.490, 121, 3.5)
    moonphases_text = f"🌑 🌓 🌕 🌗  {t('legend_moonphases')}"
    scribus.setText(moonphases_text, moonphases_frame)
    scribus.setParagraphStyle("text_left_par_style", moonphases_frame)
    scribus.selectText(0, 10, moonphases_frame)
    scribus.setCharacterStyle("moonphase_ch_style")

    _draw_planet_frame(144.741, f"<  {t('legend_mooneclipses')}")
    _draw_planet_frame(148.992, f"A  {t('sun')}")
    _draw_planet_frame(153.243, f"B  {t('moon')}")
    _draw_planet_frame(157.494, f"C  {t('mercury')}")
    _draw_planet_frame(161.745, f"D  {t('venus')}")
    _draw_planet_frame(165.996, f"E  {t('mars')}")
    _draw_planet_frame(170.247, f"F  {t('jupiter')}")
    _draw_planet_frame(174.498, f"G  {t('saturn')}")
    _draw_planet_frame(178.626, f"H  {t('uranus')}")
    _draw_planet_frame(183.582, f"I  {t('neptune')}")
    _draw_acronym_frame(148.992, f"mew  {t('maj_elon_west')}", "mew")
    _draw_acronym_frame(153.243, f"mee  {t('maj_elon_east')}", "mee")
    _draw_acronym_frame(157.494, f"sup conj  {t('sup_conj')}", "sup conj")
    _draw_acronym_frame(161.745, f"inf conj  {t('inf_conj')}", "inf conj")
    _draw_acronym_frame(165.996, f"conj  {t('conj')}", "conj")
    _draw_acronym_frame(170.247, f"opp  {t('opp')}", "opp")
    _draw_acronym_frame(174.498, f"ecl tot  {t('ecl_tot')}", "ecl tot")
    _draw_acronym_frame(178.626, f"ecl par  {t('ecl_par')}", "ecl par")
    _draw_acronym_frame(183.582, f"ecl pen  {t('ecl_pen')}", "ecl pen")

    explanation_frame = scribus.createText(17, 187.335, 121, 12.461)
    scribus.setText(fill(t("legend_explanation"), city=t("capital")), explanation_frame)
    scribus.setFont("Simoncini Garamond Std Roman", explanation_frame)
    scribus.setParagraphStyle("title_explanation_par_style", explanation_frame)
    scribus.setTextVerticalAlignment(scribus.ALIGNV_BOTTOM, explanation_frame)


def drawSecondPage(data, language):
    # --- HELPER FUNCTIONS ---
    def _get_date_parts(date_obj_or_str):
        """Restituisce le parti della data (Y, m, d, H, M, S). Accetta datetime o str."""
        if isinstance(date_obj_or_str, str):
            try:
                dt = datetime.datetime.strptime(date_obj_or_str, "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                dt = datetime.datetime.strptime(date_obj_or_str, "%Y-%m-%d")
        else:
            dt = date_obj_or_str

        return (
            dt.strftime("%Y"),
            dt.strftime("%m"),
            dt.strftime("%d"),
            dt.strftime("%H"),
            dt.strftime("%M"),
            dt.strftime("%S"),
        )

    def _draw_frame(x, y, w, h, text, style):
        """Crea un frame Scribus, imposta testo e stile, ridimensiona e restituisce l'altezza."""
        if not text:
            return 0
        frame = scribus.createText(x, y, w, h)
        scribus.setText(text, frame)
        scribus.setParagraphStyle(style, frame)
        return resize_height(
            frame
        )  # Assumo che questa funzione esista nel contesto globale

    def _format_event_line(item, p_key):
        """Formatta la riga dell'evento per la colonna centrale."""
        text = item["event"].lower().replace("_", " ")

        # Logiche specifiche per pianeta
        if p_key in ["mercury", "venus"] and "degree" in item:
            text += f" {item['degree']:.1f}°"
        elif p_key == "moon":
            moon_phases = ["C", "B", "A"]
            text += f" {moon_phases[int(item['type'])]}"

        return text

    # --- SETUP ---
    t = translator(language)
    months = constants.MONTHS
    planets = extract_planetary_events(data)

    # --temp / debug
    planets_filename = generate_filename(prefix="planets_", ext=".py")
    save_to_file(planets, planets_filename)
    # --remove before release--/

    current_y = 10
    y_gap = 2

    # --- 1. SEZIONE PASQUA ED EQUINOZI (Gestita a parte per formato diverso) ---
    left_text = "\n".join(
        [t("easter"), t("eq_spring"), t("eq_summer"), t("eq_autumn"), t("eq_winter")]
    )

    right_lines = []
    # Pasqua
    if "easter" in planets:
        _, m, d, _, _, _ = _get_date_parts(planets["easter"])
        right_lines.append(f"{d} {t(months[int(m) - 1])}")
    # Stagioni
    if "seasons" in planets:
        for season in planets["seasons"]:
            _, m, d, _, _, _ = _get_date_parts(season["date"])
            right_lines.append(f"{d} {t(months[int(m) - 1])}")

    h_left = _draw_frame(10, current_y, 50, 100, left_text, "planets_bold_par_style")
    h_right = _draw_frame(
        82, current_y, 49, 120, "\n".join(right_lines), "planets_left_par_style"
    )

    current_y += max(h_left, h_right) + y_gap

    # --- 2. SEZIONE PIANETI (Ciclo generico) ---
    # Lista ordinata delle chiavi dei pianeti da processare
    planet_keys = list(map(lambda p: p.lower(), constants.PLANETS))

    for p_key in planet_keys:
        items = planets.get(p_key)
        if not items:
            continue

        # Preparazione testi
        # Sinistra: Nome pianeta
        text_left = t(p_key)

        # Centro: Descrizione eventi
        center_lines = [_format_event_line(item, p_key) for item in items]
        text_center = "\n".join(center_lines)

        # Destra: Date e Ore
        right_lines = []
        for item in items:
            # Gestisce sia datetime objects che stringhe nel dizionario originale
            d_obj = item["date"]
            _, m, d, H, M, _ = _get_date_parts(d_obj)
            right_lines.append(f"{d} {t(months[int(m) - 1])} h{H}:{M}")
        text_right = "\n".join(right_lines)

        # Disegno frames
        # Nota: usiamo current_y calcolato dal blocco precedente
        h_l = _draw_frame(10, current_y, 40, 100, text_left, "planets_bold_par_style")
        h_c = _draw_frame(
            51, current_y, 30, 100, text_center, "planets_smallcaps_par_style"
        )
        h_r = _draw_frame(82, current_y, 49, 100, text_right, "planets_left_par_style")

        # Aggiornamento Y per il prossimo giro
        current_y += max(h_l, h_c, h_r) + y_gap


def create_planner_A5(data, language):
    """
    Orchestrates the creation of the entire A5 Planner.

    Iterates through chunks of days, creates new pages in Scribus,
    and handles progress bars.
    """
    # --temp / debug
    # logger = Logger()
    # logger.log('start')
    # --remove before release--/
    filename = generate_filename(prefix="AG_", ext=".sla")
    page_data_list = split_list(data)
    total_pages = len(page_data_list) + 2

    scribus.statusMessage("")

    create_A5_document()
    scribus.setRedraw(False)  # Optimize performance by disabling redraw
    createLineStyles()
    createTextStyles()
    scribus.saveDocAs(filename)

    drawFirstPage(data, language)
    scribus.newPage(-1)
    drawSecondPage(data, language)

    for item in page_data_list:
        current_page = scribus.currentPage()
        if current_page < total_pages:
            scribus.newPage(-1)
            pagesQty = scribus.pageCount()
            # --temp / debug
            # logger.log(f"starting page {current_page}")
            # logger.logmem()
            # --remove before release--/
            msg = fill(
                ui_t("planner_page_elaborating"),
                pagesQty=pagesQty,
                total_pages=total_pages,
            )
            scribus.statusMessage(msg)
            # Scribus getPageType: 2 for Right pages, 0 for Left pages
            if scribus.getPageType(current_page) == 2:
                draw_page("right", item)
            elif scribus.getPageType(current_page) == 0:
                draw_page("left", item)
            else:
                scribus.messageBox(
                    ui_t("mainform_title"),
                    fill(ui_t("err_unknown_page_type"), current_page=current_page),
                    scribus.ICON_CRITICAL,
                )
                sys.exit(1)
            if (current_page > 0) and (current_page % 4 == 0):
                scribus.saveDoc()
    if scribus.haveDoc():
        scribus.saveDoc()

    # --temp / debug
    # logger.log("END")
    # logger.logmem()
    # --remove before release--/
