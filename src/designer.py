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
from .utilities import template_replace, round_dt_to_min, generate_filename, save_to_file
#--temp / debug
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
    scribus.createCharStyle(name='smallcaps_ch_style', font='Simoncini Garamond Std Roman', fontsize=8.30, features='smallcaps')
    scribus.createCharStyle(name='bold_ch_style', font='Simoncini Garamond Std Bold', fontsize=8.30)
    scribus.createCharStyle(name='bold10_ch_style', font='Simoncini Garamond Std Bold', fontsize=10)
    scribus.createCharStyle(name='smallcaps10_ch_style', font='Simoncini Garamond Std Roman', fontsize=10, features='smallcaps')
    scribus.createCharStyle(name='text10_ch_style', font='Simoncini Garamond Std Roman', fontsize=10)

    scribus.createParagraphStyle('title_par_style', 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 'title_ch_style')
    scribus.createParagraphStyle('header_left_par_style', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'header_ch_style')
    scribus.createParagraphStyle('header_right_par_style', 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 'header_ch_style')
    scribus.createParagraphStyle('weekday_par_style', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'weekday_ch_style')
    scribus.createParagraphStyle('text_left_par_style', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'text_ch_style')
    scribus.createParagraphStyle('text_right_par_style', 1, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 'text_ch_style')
    scribus.createParagraphStyle('title_explanation_par_style', 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'text_ch_style')
    scribus.createParagraphStyle('text_smallcaps_par_style', 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'smallcaps_ch_style')
    scribus.createParagraphStyle('text_bold_par_style', 0, 10, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'bold_ch_style')
    scribus.createParagraphStyle('planets_bold_par_style', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'bold10_ch_style')
    scribus.createParagraphStyle('planets_smallcaps_par_style', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'smallcaps10_ch_style')
    scribus.createParagraphStyle('planets_left_par_style', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 'text10_ch_style')


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
        "saturn": []
    }

    for entry in input_data:
        # --- PASQUA ---
        if entry.get("is_easter"):
            m = str(entry['month']).zfill(2)
            d = str(entry['day']).zfill(2)
            full_date_str = f"{entry['year']}-{m}-{d}"
            result["easter"] = full_date_str
        
        # --- EQUINOZI ---
        if entry.get("season"):
            m = str(entry['month']).zfill(2)
            d = str(entry['day']).zfill(2)
            full_date_str = f"{entry['year']}-{m}-{d}"
            result['seasons'].append({
                "date": full_date_str,
                "event": entry['season_type']
            })

        # --- PIANETI INTERNI ---
        for ip in ['mercury', 'venus']:
          # Congiunzioni
          if entry.get(f"{ip}_oc_type"):
              event = "INF_CONJ" if entry[f"{ip}_oc_type"] == "ic" else "SUP_CONJ"
              result[ip].append({
                  "date": entry[f"{ip}_oc_time"],
                  "event": event
              })
          
          # Elongazioni massime
          if entry.get(f"{ip}_elong_direction"):
              event = "MEE" if entry[f"{ip}_elong_direction"] == "east" else "MEW"
              result[ip].append({
                  "date": entry[f"{ip}_elong_time"],
                  "event": event,
                  "degree": entry[f"{ip}_elong_degrees"]
              })

        # --- LUNA (Eclissi) ---
        if entry.get("moon_eclipse_type_num"):
            m = str(entry['month']).zfill(2)
            d = str(entry['day']).zfill(2)
            full_date_str = f"{entry['year']}-{m}-{d} {entry['moon_eclipse_time']}"
            result["moon"].append({
                "date": full_date_str,
                "event": "MOON_ECL",
                "type": entry["moon_eclipse_type_num"]
            })

        # --- PIANETI ESTERNI ---
        # Congiunzioni
        for ep in ['mars', 'jupiter', 'saturn']:
          if entry.get(f"{ep}_oc_type"):
              event = "CONJ" if entry[f"{ep}_oc_type"] == "c" else "OPP"
              result[ep].append({
                  "date": entry[f"{ep}_oc_time"],
                  "event": event
              })

    return result


def drawFirstPage(data, language):
    def _draw_planet_frame(ypos, text):
        text_frame = scribus.createText(17, ypos, 121, 3.5)
        scribus.setText(text, text_frame)
        scribus.setParagraphStyle('text_left_par_style', text_frame)
        scribus.selectText(0, 1, text_frame)
        scribus.setCharacterStyle('ephem_sym_ch_style')

    t = translator(language)
    year = get_main_year(data)

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


def drawSecondPage(data, language):
    # --- HELPER FUNCTIONS ---
    def _get_date_parts(date_obj_or_str):
        """Restituisce le parti della data (Y, m, d, H, M, S). Accetta datetime o str."""
        if isinstance(date_obj_or_str, str):
            try:
                dt = datetime.datetime.strptime(date_obj_or_str, '%Y-%m-%d %H:%M:%S.%f')
            except ValueError:
                dt = datetime.datetime.strptime(date_obj_or_str, '%Y-%m-%d')
        else:
            dt = date_obj_or_str
        
        return (
            dt.strftime('%Y'), dt.strftime('%m'), dt.strftime('%d'),
            dt.strftime('%H'), dt.strftime('%M'), dt.strftime('%S')
        )

    def _draw_frame(x, y, w, h, text, style):
        """Crea un frame Scribus, imposta testo e stile, ridimensiona e restituisce l'altezza."""
        if not text: return 0
        frame = scribus.createText(x, y, w, h)
        scribus.setText(text, frame)
        scribus.setParagraphStyle(style, frame)
        return resize_height(frame) # Assumo che questa funzione esista nel contesto globale

    def _format_event_line(item, p_key):
        """Formatta la riga dell'evento per la colonna centrale."""
        text = item["event"].lower().replace("_", " ")
        
        # Logiche specifiche per pianeta
        if p_key in ["mercury", "venus"] and item.get("degree"):
            text += f" {item['degree']:.1f}°"
        elif p_key == "moon":
            moon_phases = ["C", "B", "A"]
            text += f" {moon_phases[int(item['type'])]}"
            
        return text

    # --- SETUP ---
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    t = translator(language)
    planets = extract_planetary_events(data)
    
    #--temp / debug
    planets_filename = generate_filename(prefix='planets_', ext='.py')
    save_to_file(planets, planets_filename)
    #--remove before release--/ 
    
    current_y = 10
    y_gap = 2

    # --- 1. SEZIONE PASQUA ED EQUINOZI (Gestita a parte per formato diverso) ---
    left_text = "\n".join([t('easter'), t('eq_spring'), t('eq_summer'), t('eq_autumn'), t('eq_winter')])
    
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

    h_left = _draw_frame(10, current_y, 40, 100, left_text, 'planets_bold_par_style')
    h_right = _draw_frame(82, current_y, 49, 120, "\n".join(right_lines), 'planets_left_par_style')
    
    current_y += max(h_left, h_right) + y_gap

    # --- 2. SEZIONE PIANETI (Ciclo generico) ---
    # Lista ordinata delle chiavi dei pianeti da processare
    planet_keys = ["mercury", "venus", "moon", "mars", "jupiter", "saturn"]

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
        h_l = _draw_frame(10, current_y, 40, 100, text_left, 'planets_bold_par_style')
        h_c = _draw_frame(51, current_y, 30, 100, text_center, 'planets_smallcaps_par_style')
        h_r = _draw_frame(82, current_y, 49, 100, text_right, 'planets_left_par_style')

        # Aggiornamento Y per il prossimo giro
        current_y += max(h_l, h_c, h_r) + y_gap
    

# def drawSecondPage(data, language):
#     def _date_str(stringa_data):
#         try:
#             dt = datetime.datetime.strptime(stringa_data, '%Y-%m-%d %H:%M:%S.%f')
#         except ValueError:
#             dt = datetime.datetime.strptime(stringa_data, '%Y-%m-%d')
#         return (
#             dt.strftime('%Y'), 
#             dt.strftime('%m'), 
#             dt.strftime('%d'), 
#             dt.strftime('%H'), 
#             dt.strftime('%M'), 
#             dt.strftime('%S')
#         )

#     months = ['January', 'February', 'March', 'April',
#               'May', 'June', 'July', 'August',
#               'September', 'October', 'November', 'December']
#     t = translator(language)
#     y_gap = 2
#     planets = extract_planetary_events(data)

#     #--temp / debug
#     planets_filename = generate_filename(prefix='planets_', ext='.py')
#     save_to_file(planets, planets_filename)
#     #--remove before release--/

#     # --- PASQUA ED EQUINOZI ---
#     # frame sinistra
#     seasons_left_text = (
#         f"{t('easter')}\n"
#         f"{t('eq_spring')}\n"
#         f"{t('eq_summer')}\n"
#         f"{t('eq_autumn')}\n"
#         f"{t('eq_winter')}"
#     )
#     season_left_frame = scribus.createText(10, 10, 40, 100)
#     scribus.setText(seasons_left_text, season_left_frame)
#     scribus.setParagraphStyle('planets_bold_par_style', season_left_frame)
#     season_left_frame_height = resize_height(season_left_frame)
#     season_left_frame_width = resize_width(season_left_frame)
#     # frame destra
#     seasons_right_text = ""
#     for item in planets.keys():
#         if item == "easter":
#             _, month, day, _, _, _ = _date_str(planets["easter"])
#             seasons_right_text += f"{day} {t(months[int(month) - 1])}\n"
#         elif item == 'seasons':
#             for season in planets["seasons"]:
#                 _, month, day, _, _, _ = _date_str(season["date"])
#                 seasons_right_text += f"{day} {t(months[int(month) - 1])}\n"
#     if seasons_right_text.endswith("\n"):
#         seasons_right_text = seasons_right_text[:-1]
    
#     season_right_frame = scribus.createText(82, 10, 49, 120)
#     scribus.setText(seasons_right_text, season_right_frame)
#     scribus.setParagraphStyle('planets_left_par_style', season_right_frame)
#     season_right_frame_height = resize_height(season_right_frame)
#     last_max_y = max([season_right_frame_height, season_left_frame_height])

#     # --- MERCURIO ---
#     if planets["mercury"]:
#         mercury_frame_y = 10 + y_gap + last_max_y
#         # frame sinistra
#         mercury_left_text = f"{t("mercury")}"
#         mercury_left_frame = scribus.createText(10, mercury_frame_y, 40, 100)
#         scribus.setText(mercury_left_text, mercury_left_frame)
#         scribus.setParagraphStyle('planets_bold_par_style', mercury_left_frame)
#         mercury_left_frame_height = resize_height(mercury_left_frame)
#         # frame centro
#         mercury_center_text = ""
#         for item in planets["mercury"]:
#             mercury_center_text += f"{item["event"].lower().replace("_", " ")}"
#             if item.get("degree"):
#                 mercury_center_text += f" {item["degree"]:.1f}°\n"
#             else:
#                 mercury_center_text += "\n"
#         if mercury_center_text.endswith("\n"):
#             mercury_center_text = mercury_center_text[:-1]
#         mercury_center_frame = scribus.createText(51, mercury_frame_y, 30, 100)
#         scribus.setText(mercury_center_text, mercury_center_frame)
#         scribus.setParagraphStyle('planets_smallcaps_par_style', mercury_center_frame)
#         mercury_center_frame_height = resize_height(mercury_center_frame)
#         # frame destra
#         mercury_right_text = ""
#         for item in planets["mercury"]:
#             _, month, day, hour, minute, _ = _date_str(item["date"].strftime("%Y-%m-%d %H:%M:%S.%f"))
#             mercury_right_text += f"{day} {t(months[int(month) - 1])} h{hour}:{minute}\n"
#         if mercury_right_text.endswith("\n"):
#             mercury_right_text = mercury_right_text[:-1]
#         mercury_right_frame = scribus.createText(82, mercury_frame_y, 49, 100)
#         scribus.setText(mercury_right_text, mercury_right_frame)
#         scribus.setParagraphStyle('planets_left_par_style', mercury_right_frame)
#         mercury_right_frame_height = resize_height(mercury_right_frame)
#         last_max_y = mercury_frame_y + max([mercury_left_frame_height, mercury_center_frame_height, mercury_right_frame_height])

#     # --- VENERE ---
#     if planets["venus"]:
#         venus_frame_y =  y_gap + last_max_y
#         # frame sinistra
#         venus_left_text = f"{t("venus")}"
#         venus_left_frame = scribus.createText(10, venus_frame_y, 40, 100)
#         scribus.setText(venus_left_text, venus_left_frame)
#         scribus.setParagraphStyle('planets_bold_par_style', venus_left_frame)
#         venus_left_frame_height = resize_height(venus_left_frame)
#         # frame centro
#         venus_center_text = ""
#         for item in planets["venus"]:
#             venus_center_text += f"{item["event"].lower().replace("_", " ")}"
#             if item.get("degree"):
#                 venus_center_text += f" {item["degree"]:.1f}°\n"
#             else:
#                 venus_center_text += "\n"
#         if venus_center_text.endswith("\n"):
#             venus_center_text = venus_center_text[:-1]
#         venus_center_frame = scribus.createText(51, venus_frame_y, 30, 100)
#         scribus.setText(venus_center_text, venus_center_frame)
#         scribus.setParagraphStyle('planets_smallcaps_par_style', venus_center_frame)
#         venus_center_frame_height = resize_height(venus_center_frame)
#         # frame destra
#         venus_right_text = ""
#         for item in planets["venus"]:
#             _, month, day, hour, minute, _ = _date_str(item["date"].strftime("%Y-%m-%d %H:%M:%S.%f"))
#             venus_right_text += f"{day} {t(months[int(month) - 1])} h{hour}:{minute}\n"
#         if venus_right_text.endswith("\n"):
#             venus_right_text = venus_right_text[:-1]
#         venus_right_frame = scribus.createText(82, venus_frame_y, 49, 100)
#         scribus.setText(venus_right_text, venus_right_frame)
#         scribus.setParagraphStyle('planets_left_par_style', venus_right_frame)
#         venus_right_frame_height = resize_height(venus_right_frame)
#         last_max_y = venus_frame_y + max([venus_left_frame_height, venus_center_frame_height, venus_right_frame_height])

#     # --- LUNA ---
#     if planets["moon"]:
#         moon_frame_y = y_gap + last_max_y
#         # frame sinistra
#         moon_left_text = f"{t("moon")}"
#         moon_left_frame = scribus.createText(10, moon_frame_y, 40, 100)
#         scribus.setText(moon_left_text, moon_left_frame)
#         scribus.setParagraphStyle('planets_bold_par_style', moon_left_frame)
#         moon_left_frame_height = resize_height(moon_left_frame)
#         # frame centro
#         moon_center_text = ""
#         for item in planets["moon"]:
#             moon_center_text += f"{item["event"].lower().replace("_", " ")} {["C", "B", "A"][int(item["type"])]}\n"
#         if moon_center_text.endswith("\n"):
#             moon_center_text = moon_center_text[:-1]
#         moon_center_frame = scribus.createText(51, moon_frame_y, 30, 100)
#         scribus.setText(moon_center_text, moon_center_frame)
#         scribus.setParagraphStyle('planets_smallcaps_par_style', moon_center_frame)
#         moon_center_frame_height = resize_height(moon_center_frame)
#         # frame destra
#         moon_right_text = ""
#         for item in planets["moon"]:
#             _, month, day, hour, minute, _ = _date_str(item["date"])
#             moon_right_text += f"{day} {t(months[int(month) - 1])} h{hour}:{minute}\n"
#         if moon_right_text.endswith("\n"):
#             moon_right_text = moon_right_text[:-1]
#         moon_right_frame = scribus.createText(82, moon_frame_y, 49, 100)
#         scribus.setText(moon_right_text, moon_right_frame)
#         scribus.setParagraphStyle('planets_left_par_style', moon_right_frame)
#         moon_right_frame_height = resize_height(moon_right_frame)
#         last_max_y = moon_frame_y + max([moon_left_frame_height, moon_center_frame_height, moon_right_frame_height])

#     # --- MARTE ---
#     if planets["mars"]:
#         mars_frame_y = y_gap + last_max_y
#         # frame sinistra
#         mars_left_text = f"{t("mars")}"
#         mars_left_frame = scribus.createText(10, mars_frame_y, 40, 100)
#         scribus.setText(mars_left_text, mars_left_frame)
#         scribus.setParagraphStyle('planets_bold_par_style', mars_left_frame)
#         mars_left_frame_height = resize_height(mars_left_frame)
#         # frame centro
#         mars_center_text = ""
#         for item in planets["mars"]:
#             mars_center_text += f"{item["event"].lower().replace("_", " ")}\n"
#         if mars_center_text.endswith("\n"):
#             mars_center_text = mars_center_text[:-1]
#         mars_center_frame = scribus.createText(51, mars_frame_y, 30, 100)
#         scribus.setText(mars_center_text, mars_center_frame)
#         scribus.setParagraphStyle('planets_smallcaps_par_style', mars_center_frame)
#         mars_center_frame_height = resize_height(mars_center_frame)
#         # frame destra
#         mars_right_text = ""
#         for item in planets["mars"]:
#             _, month, day, hour, minute, _ = _date_str(item["date"].strftime("%Y-%m-%d %H:%M:%S.%f"))
#             mars_right_text += f"{day} {t(months[int(month) - 1])} h{hour}:{minute}\n"
#         if mars_right_text.endswith("\n"):
#             mars_right_text = mars_right_text[:-1]
#         mars_right_frame = scribus.createText(82, mars_frame_y, 49, 100)
#         scribus.setText(mars_right_text, mars_right_frame)
#         scribus.setParagraphStyle('planets_left_par_style', mars_right_frame)
#         mars_right_frame_height = resize_height(mars_right_frame)
#         last_max_y = mars_frame_y + max([mars_left_frame_height, mars_center_frame_height, mars_right_frame_height])

#     # --- GIOVE ---
#     if planets["jupiter"]:
#         jupiter_frame_y = y_gap + last_max_y
#         # frame sinistra
#         jupiter_left_text = f"{t("jupiter")}"
#         jupiter_left_frame = scribus.createText(10, jupiter_frame_y, 40, 100)
#         scribus.setText(jupiter_left_text, jupiter_left_frame)
#         scribus.setParagraphStyle('planets_bold_par_style', jupiter_left_frame)
#         jupiter_left_frame_height = resize_height(jupiter_left_frame)
#         # frame centro
#         jupiter_center_text = ""
#         for item in planets["jupiter"]:
#             jupiter_center_text += f"{item["event"].lower().replace("_", " ")}\n"
#         if jupiter_center_text.endswith("\n"):
#             jupiter_center_text = jupiter_center_text[:-1]
#         jupiter_center_frame = scribus.createText(51, jupiter_frame_y, 30, 100)
#         scribus.setText(jupiter_center_text, jupiter_center_frame)
#         scribus.setParagraphStyle('planets_smallcaps_par_style', jupiter_center_frame)
#         jupiter_center_frame_height = resize_height(jupiter_center_frame)
#         # frame destra
#         jupiter_right_text = ""
#         for item in planets["jupiter"]:
#             _, month, day, hour, minute, _ = _date_str(item["date"].strftime("%Y-%m-%d %H:%M:%S.%f"))
#             jupiter_right_text += f"{day} {t(months[int(month) - 1])} h{hour}:{minute}\n"
#         if jupiter_right_text.endswith("\n"):
#             jupiter_right_text = jupiter_right_text[:-1]
#         jupiter_right_frame = scribus.createText(82, jupiter_frame_y, 49, 100)
#         scribus.setText(jupiter_right_text, jupiter_right_frame)
#         scribus.setParagraphStyle('planets_left_par_style', jupiter_right_frame)
#         jupiter_right_frame_height = resize_height(jupiter_right_frame)
#         last_max_y = jupiter_frame_y + max([jupiter_left_frame_height, jupiter_center_frame_height, jupiter_right_frame_height])

#     # --- SATURNO ---
#     if planets["saturn"]:
#         saturn_frame_y = y_gap + last_max_y
#         # frame sinistra
#         saturn_left_text = f"{t("saturn")}"
#         saturn_left_frame = scribus.createText(10, saturn_frame_y, 40, 100)
#         scribus.setText(saturn_left_text, saturn_left_frame)
#         scribus.setParagraphStyle('planets_bold_par_style', saturn_left_frame)
#         saturn_left_frame_height = resize_height(saturn_left_frame)
#         # frame centro
#         saturn_center_text = ""
#         for item in planets["saturn"]:
#             saturn_center_text += f"{item["event"].lower().replace("_", " ")}\n"
#         if saturn_center_text.endswith("\n"):
#             saturn_center_text = saturn_center_text[:-1]
#         saturn_center_frame = scribus.createText(51, saturn_frame_y, 30, 100)
#         scribus.setText(saturn_center_text, saturn_center_frame)
#         scribus.setParagraphStyle('planets_smallcaps_par_style', saturn_center_frame)
#         saturn_center_frame_height = resize_height(saturn_center_frame)
#         # frame destra
#         saturn_right_text = ""
#         for item in planets["saturn"]:
#             _, month, day, hour, minute, _ = _date_str(item["date"].strftime("%Y-%m-%d %H:%M:%S.%f"))
#             saturn_right_text += f"{day} {t(months[int(month) - 1])} h{hour}:{minute}\n"
#         if saturn_right_text.endswith("\n"):
#             saturn_right_text = saturn_right_text[:-1]
#         saturn_right_frame = scribus.createText(82, saturn_frame_y, 49, 100)
#         scribus.setText(saturn_right_text, saturn_right_frame)
#         scribus.setParagraphStyle('planets_left_par_style', saturn_right_frame)
#         saturn_right_frame_height = resize_height(saturn_right_frame)
#         last_max_y = saturn_frame_y + max([saturn_left_frame_height, saturn_center_frame_height, saturn_right_frame_height])


def create_planner_A5(data, language):
    """
    Orchestrates the creation of the entire A5 Planner.

    Iterates through chunks of days, creates new pages in Scribus,
    and handles progress bars.
    """
    #--temp / debug
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

    # scribus.progressSet(1)
    drawFirstPage(data, language)
    scribus.newPage(-1)
    drawSecondPage(data, language)

    # for item in page_data_list:
    #     current_page = scribus.currentPage()
    #     if current_page < total_pages:
    #         scribus.newPage(-1)
    #         pagesQty = scribus.pageCount()
    #         # scribus.progressSet(pagesQty if pagesQty <= total_pages else total_pages)
    #         #--temp / debug
    #         logger.log(f"starting page {current_page}")
    #         logger.logmem()
    #         #--remove before release--/
    #         msg = template_replace(ui_t("planner_page_elaborating"), pagesQty=pagesQty, total_pages=total_pages)
    #         scribus.statusMessage(msg)
    #         # Scribus getPageType: 2 for Right pages, 0 for Left pages
    #         if scribus.getPageType(current_page) == 2:
    #             draw_page('right', item)
    #         elif scribus.getPageType(current_page) == 0:
    #             draw_page('left', item)
    #         else:
    #             scribus.messageBox(
    #                 "Planner Generator",
    #                 f"Error: unknown page type for page {current_page}.",
    #                 scribus.ICON_CRITICAL,
    #             )
    #             sys.exit(1)
    #         if ((current_page > 0) and (current_page % 4 == 0)):
    #             scribus.saveDoc()
    if scribus.haveDoc():
        scribus.saveDoc()
    
    #--temp / debug
    logger.log("END")
    logger.logmem()
    #--remove before release--/
