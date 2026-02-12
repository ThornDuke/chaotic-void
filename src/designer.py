# -*- coding: utf-8 -*-
"""
Planner Layout Designer Module.
This module handles the visual generation of the planner within Scribus,
managing page creation, drawing lines, and placing text frames for
dates, holidays, astronomical data, and seasons.
"""

from calendar import calendar
import sys
import datetime
import re
import scribus  # pyright: ignore[reportMissingImports]
from .data.lines import get_A5_line_data
from .data.localization import translator, by_acronym
from .utilities import template_replace, round_dt_to_min, generate_filename
#--temp
from src.archivist import Logger
#--remove before release--/

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
    scribus.createCustomLineStyle('thin', [{'Color': 'Black', 'Width': 0.33}])
    scribus.createCustomLineStyle('thick', [{'Color': 'Black', 'Width': 1}])


def createTextStyles():
    """
    Define and create all necessary Character and Paragraph styles in Scribus.
    
    Sets up typography for titles, headers, weekdays, moon phases, 
    and ephemeris symbols using specific font families and sizes.
    """
    scribus.createCharStyle(name='title_ch_style', font='Simoncini Garamond Std Roman', fontsize=34)
    scribus.createCharStyle(name='header_ch_style', font='Simoncini Garamond Std Roman', fontsize=21)
    scribus.createCharStyle(name='weekday_ch_style', font='Simoncini Garamond Std Bold', fontsize=8.30)
    scribus.createCharStyle(name='text_ch_style', font='Simoncini Garamond Std Roman', fontsize=8.30)
    scribus.createCharStyle(name='moonphase_ch_style', font='Symbola Regular', fontsize=8.30)
    scribus.createCharStyle(name='ephem_sym_ch_style', font='AstroGadget Regular', fontsize=8.30)

    scribus.createParagraphStyle('title_par_style', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'title_ch_style')
    scribus.createParagraphStyle('header_left_par_style', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'header_ch_style')
    scribus.createParagraphStyle('header_right_par_style', 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 'header_ch_style')
    scribus.createParagraphStyle('weekday_par_style', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'weekday_ch_style')
    scribus.createParagraphStyle('text_left_par_style', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'text_ch_style')
    scribus.createParagraphStyle('text_right_par_style', 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 'text_ch_style')
    scribus.createParagraphStyle('title_explanation_par_style', 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'text_ch_style')


def draw_lines(side):
    """
    Draws the background grid lines for a page.

    Args:
      side (str): 'left' or 'right' to determine line coordinates and specific vertical lines.
    """
    line_data = get_A5_line_data(side)
    for data in line_data:
        line = scribus.createLine(data["x"], data["y"], data["x"] + data["w"], data["y"])
        scribus.setCustomLineStyle('thick' if data["th"] == 1 else 'thin', line)

    if side == "right":
        # Additional vertical separator for the right page (weekend section)
        vline = scribus.createLine(77.5, 139.361, 77.5, 139.361 + 60.639)
        scribus.setCustomLineStyle('thin', vline)


def split_list(input_list):
    """
    Splits the list of days into chunks of 3 and 4 to fit facing pages.
    Left pages usually take 3 days, right pages take 4 (including the weekend split).

    Args:
      input_list (list): The complete list of days.

    Returns:
      list[list]: A list of chunks (alternating sizes 3 and 4).
    """
    result = []
    i = 0
    is_three = True  # Starts with a group of 3

    while i < len(input_list):
        if is_three:
            result.append(input_list[i : i + 3])
            i += 3
        else:
            result.append(input_list[i : i + 4])
            i += 4
        is_three = not is_three

    return result


def draw_weekday_frame(x, y, w, h, text):
    """Creates a text frame for the weekday name and day number."""
    text_frame = scribus.createText(x, y, w, h)
    scribus.setText(text, text_frame)
    scribus.setParagraphStyle('weekday_par_style', text_frame)


def draw_holyday_frame(x, y, w, h, text):
    """Creates a text frame for holiday names."""
    text_frame = scribus.createText(x, y, w, h)
    scribus.setText(text, text_frame)
    scribus.setParagraphStyle('text_left_par_style', text_frame)


def draw_season_frame(x, y, w, h, text):
    """Creates a text frame for seasons (Equinoxes/Solstices)."""
    text_frame = scribus.createText(x, y, w, h)
    scribus.setText(text, text_frame)
    scribus.setParagraphStyle('text_right_par_style', text_frame)


def draw_moon_phases_frame(x, y, w, h, moon_phase, phase_time):
    """
    Creates a text frame with lunar symbols and times.
    Uses the 'Symbola' font for correctly rendering astronomical glyphs.
    """
    if moon_phase == '':
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
    scribus.setParagraphStyle('text_right_par_style', text_frame)

    # Format symbols with specialized font
    moon_index = text.find(moon_symbol)
    scribus.selectText(moon_index + 1, 1, text_frame)
    scribus.setCharacterStyle('moonphase_ch_style')


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
    planets = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]

    # --- 1. Draw planets Frame ---
    for i, planet in enumerate(planets):
        current_y = y_pos + (y_gap * i)
        # Symbols correspond to 'A' (Sun) through 'G' (Saturn).
        # ord('A') is 65. We generate the char dynamically based on index.
        symbol_char = chr(65 + i)
        ephem_text = f"{symbol_char}"
        is_visible = datadict.get(f"{planet}_isvisible", False)
        if is_visible:
            # specific keys retrieval
            p_rise = datadict.get(f"{planet}_rise", "")
            p_rise_time = hour_min(p_rise) if p_rise != "" else ""
            p_transit = datadict.get(f"{planet}_transit", "")
            p_transit_time = hour_min(p_transit) if p_transit != "" else ""
            p_set = datadict.get(f"{planet}_set", "")
            p_set_time = hour_min(p_set) if p_set != "" else ""
            ephem_text = f"{symbol_char}  {p_rise_time}  {p_transit_time}  {p_set_time}"
            ephem_frame = scribus.createText(x_pos, current_y, 30, 3)
            scribus.setText(ephem_text, ephem_frame)
            scribus.setParagraphStyle('text_right_par_style', ephem_frame)
            scribus.selectText(0, 1, ephem_frame)
            scribus.setCharacterStyle('ephem_sym_ch_style')

    # --- 2. Draw moon eclipse data, if present ---
    if "moon_eclipse_type_num" in datadict:
        # moon_eclipse_type_num: 0 -> penumbral -> C; 1 -> parzial -> B; 2 -> total -> A
        moonecl_text = f"<  {chr(67 - datadict['moon_eclipse_type_num'])}  {hour_min(datadict['moon_eclipse_time'])}"
        moonecl_frame = scribus.createText(x_pos, y_pos - y_gap, 30, 3)
        scribus.setText(moonecl_text, moonecl_frame)
        scribus.setParagraphStyle('text_right_par_style', moonecl_frame)
        scribus.selectText(0, 1, moonecl_frame)
        scribus.setCharacterStyle('ephem_sym_ch_style')


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
    year_string = str(items[0]["year"])
    month_string = items[0]["translated_month"]

    # Month header
    month_frame = scribus.createText(10 if side == 'left' else 88.152, 10, 49.848, 8)
    scribus.setText(month_string, month_frame)
    scribus.setParagraphStyle(f"header_{side}_par_style", month_frame)

    # Year header
    year_frame = scribus.createText(104.781 if side == 'left' else 17, 10, 26.219, 8)
    scribus.setText(year_string, year_frame)
    scribus.setParagraphStyle(f"header_{'right' if side == 'left' else 'left'}_par_style", year_frame)

    draw_lines(side)

    for i in range(3):
        y_offset = 19.521 + (i * 60.562)        
        # weekday frames
        draw_weekday_frame(10 if side == 'left' else 17, y_offset, 60, 3.5,
                           f"{items[i]['translated_weekday']} {items[i]['day']}")        

        # Moon data
        # Special coordinates for the third day (sharing row with the fourth)
        if side == 'right':
            sun_x = 17.575 if i == 2 else 78
            draw_moon_phases_frame(sun_x, y_offset, 60, 3.5, f"{items[i].get('phase', '')}", items[i].get('phase_time', ''))
        else:
            draw_moon_phases_frame(71, y_offset, 60, 3.5, f"{items[i].get('phase', '')}", items[i].get('phase_time', ''))
        
        # holidays
        if "holiday_name" in items[i]:
            draw_holyday_frame(10 if side == 'left' else 17, y_offset + 5.073, 60, 3.5,
                               items[i]["holiday_name"])
            
        # Season
        if "season" in items[i]:
            if side == 'right':
                season_x = 17.575 if i == 2 else 78
                draw_season_frame(season_x, y_offset + 5.073, 60, 3.5, items[i]["season"])
            else:
                draw_season_frame(71, y_offset + 5.073, 60, 3.5, items[i]["season"])
        
        # Planets Ephemeris
        if side == 'left':
            draw_planets_ephemeris(101, 45.464 + (i * 60.537), items[i])
        
    if side == 'right': # out of the cicle because draw a full page
        draw_planets_ephemeris(108, 45.464, items[0])
        draw_planets_ephemeris(108, 106.001, items[1])
        draw_planets_ephemeris(47.324, 166.538, items[2])
        draw_planets_ephemeris(108, 166.538, items[3])
    
    # Handle the 4th day specifically (left column of the last row)
    if side == 'right':
        draw_weekday_frame(77.425, 140.637, 60, 3.5,
            f"{items[3]['translated_weekday']} {items[3]['day']}")
        draw_moon_phases_frame(78, 140.637, 60, 3.5,
            f"{items[3]['phase'] if 'phase' in items[3] else ''}",
            f"{hour_min(items[3]['phase_time']) if 'phase_time' in items[3] else ''}")
        if "holiday_name" in items[3]:
            draw_holyday_frame(77.725, 145.710, 60, 3.5, items[3]["holiday_name"])
        if "season" in items[3]:
            draw_season_frame(78, 145.710, 60, 3.5, items[3]["season"])


def get_main_year(data):
    """Finds the primary year by looking for January 1st."""
    first_day = next(
        (item for item in data if item["month"] == 1 and item["day"] == 1), None
    )
    return first_day["year"] if first_day else None


def drawFirstPage(year, language):
    """Creates a centered cover page title with the planner year an a legend with the symbols used."""
    def _draw_planet_frame(ypos, text):
        text_frame = scribus.createText(17, ypos, 121, 3.5)
        scribus.setText(text, text_frame)
        scribus.setParagraphStyle('text_left_par_style', text_frame)
        scribus.selectText(0, 1, text_frame)
        scribus.setCharacterStyle('ephem_sym_ch_style')

    t = translator(language)

    title_frame = scribus.createText(17, 80.213, 121, 12.803)
    scribus.setText(f"{year}", title_frame)
    scribus.setParagraphStyle('title_par_style', title_frame)

    legend_frame = scribus.createText(17, 144.240, 121, 3.5)
    scribus.setText(f"{t('legend')}", legend_frame)
    scribus.setParagraphStyle('text_left_par_style', legend_frame)

    moonphases_frame = scribus.createText(17, 148.490, 121, 3.5)
    moonphases_text = f"🌑 🌓 🌕 🌗  {t('legend_moonphases')}"
    scribus.setText(moonphases_text, moonphases_frame)
    scribus.setParagraphStyle('text_left_par_style', moonphases_frame)
    scribus.selectText(0, 10, moonphases_frame)
    scribus.setCharacterStyle('moonphase_ch_style')

    _draw_planet_frame(152.741, f"<  {t('legend_mooneclipses')}")
    _draw_planet_frame(156.992, f"A  {t('sun')}")
    _draw_planet_frame(161.243, f"B  {t('moon')}")
    _draw_planet_frame(165.494, f"C  {t('mercury')}")
    _draw_planet_frame(169.745, f"D  {t('venus')}")
    _draw_planet_frame(173.996, f"E  {t('mars')}")
    _draw_planet_frame(178.247, f"F  {t('jupiter')}")
    _draw_planet_frame(182.498, f"G  {t('saturn')}")

    explanation_frame = scribus.createText(17, 187.335, 121, 12.461)
    scribus.setText(template_replace(t('legend_explanation'), city=t('capital')), explanation_frame)
    scribus.setFont("Simoncini Garamond Std Roman", explanation_frame)
    scribus.setParagraphStyle('title_explanation_par_style', explanation_frame)
    scribus.setTextVerticalAlignment(scribus.ALIGNV_BOTTOM, explanation_frame)
    

def create_planner_A5(data, language):
    """
    Orchestrates the creation of the entire A5 Planner.

    Iterates through chunks of days, creates new pages in Scribus,
    and handles progress bars.
    """
    #--temp
    logger = Logger()
    logger.log('start')
    #--remove before release--/
    filename = generate_filename(prefix='AG_', ext='.sla')
    ui_t = translator(by_acronym(scribus.getGuiLanguage()))
    page_data_list = split_list(data)
    total_pages = len(page_data_list) + 1

    scribus.statusMessage("")
    # scribus.progressReset()
    # scribus.progressTotal(total_pages)

    create_A5_document()
    scribus.setRedraw(False)  # Optimize performance by disabling redraw
    createLineStyles()
    createTextStyles()
    scribus.saveDocAs(filename)

    main_year = get_main_year(data)
    # scribus.progressSet(1)
    drawFirstPage(main_year, language)

    for item in page_data_list:
        current_page = scribus.currentPage()
        if current_page < total_pages:
            scribus.newPage(-1)
            pagesQty = scribus.pageCount()
            # scribus.progressSet(pagesQty if pagesQty <= total_pages else total_pages)
            #--temp
            logger.log(f"starting page {current_page}")
            logger.logmem()
            #--remove before release--/
            msg = template_replace(ui_t("planner_page_elaborating"), pagesQty=pagesQty, total_pages=total_pages)
            scribus.statusMessage(msg)
            # Scribus getPageType: 2 for Right pages, 0 for Left pages
            if scribus.getPageType(current_page) == 2:
                draw_page('right', item)
            elif scribus.getPageType(current_page) == 0:
                draw_page('left', item)
            else:
                scribus.messageBox(
                    "Planner Generator",
                    f"Error: unknown page type for page {current_page}.",
                    scribus.ICON_CRITICAL,
                )
                sys.exit(1)
            if ((current_page > 0) and (current_page % 4 == 0)):
                scribus.saveDoc()
    if scribus.haveDoc():
        scribus.saveDoc()
    
    #--temp
    logger.log("END")
    logger.logmem()
    #--remove before release--/
