# -*- coding: utf-8 -*-
"""
Astronomical Calculations Module.
This module provides functions to calculate solar events (sunrise/sunset),
lunar phases, seasonal transitions (equinoxes/solstices), and religious
holidays (Easter) using the 'astral' and 'pyephem' libraries.
"""

import datetime
from zoneinfo import ZoneInfo
from collections import namedtuple
from skyfield import almanac, eclipselib
from skyfield.api import load, wgs84
from skyfield.framelib import ecliptic_frame
from skyfield.searchlib import find_maxima
import ephem
from .data.localization import translator

JPL_EPHEMERIS_FILE = "de440s.bsp"


def bsp_alias(planet_name, data):
    PlanetResult = namedtuple('PlanetResult', ['name', 'code'])
    
    search_name = planet_name.upper()
    barycenter_name = f"{search_name}_BARYCENTER"
    
    clean_match = None
    barycenter_match = None

    names = data.names()

    for code, aliases in names.items():
        if search_name in aliases:
            clean_match = PlanetResult(name=search_name, code=code)
            break 
        if barycenter_name in aliases:
            barycenter_match = PlanetResult(name=barycenter_name, code=code)

    if clean_match:
        return clean_match
    if barycenter_match:
        return barycenter_match
    
    raise ValueError(f"[bsp_alias]: The planet '{planet_name}' is not present in the provided dictionary.")


def opposition_conjunction(body, year, language):    
    t = translator(language)
    timezone = ZoneInfo(t("timezone"))

    l_body = body.lower()
    if l_body not in ['mars', 'jupiter', 'saturn', 'mercury', 'venus']:
        raise ValueError('[opposition_conjunction]: Oppositions and conjunctions can only be calculated for Mercury, Venus, Mars, Jupiter and Saturn')
    
    ts = load.timescale()
    planets = load(JPL_EPHEMERIS_FILE)
    planet_sign = bsp_alias(body, planets)
    
    t0 = ts.utc(year - 1, 1, 1)
    t1 = ts.utc(year + 1, 12, 31)
    f = almanac.oppositions_conjunctions(planets, planets[planet_sign.name])
    t, y = almanac.find_discrete(t0, t1, f)

    result = []
    for ti, yi in zip(t, y):
        tz_time = ti.astimezone(timezone)
        oc = int(f"{yi}")
        # oc_type:  ic -> inferior conjunction
        #           sc -> superior conjunction
        #           c -> conjunction
        #           o -> opposition
        oc_type = ''
        if oc == 0:
            if l_body in ['mercury', 'venus']:
                oc_type = 'ic'
            else:
                oc_type = 'c'
        else:
            if l_body in ['mercury', 'venus']:
                oc_type = 'sc'
            else:
                oc_type = 'o'
        result.append({
            'year': int(f"{ti.utc.year}"),
            'month': int(f"{ti.utc.month}"),
            'day': int(f"{ti.utc.day}"),
            f"{body}_oc_time": tz_time,
            f"{body}_oc": oc,
            f"{body}_oc_type": oc_type
        })
    
    return result


def max_elongation(body, year, language):
    l_body = body.lower()
    if l_body not in ['venus', 'mercury']:
        raise ValueError('[max_elongation]: The maximum elongation can only be calculated for Mercury and Venus')
    
    t = translator(language)
    timezone = ZoneInfo(t("timezone"))

    ts = load.timescale()
    t0 = ts.utc(year - 1)
    t1 = ts.utc(year + 1)

    eph = load(JPL_EPHEMERIS_FILE)
    object = bsp_alias(body, eph)
    sun, earth, curr_body = eph['sun'], eph['earth'], eph[object.name]

    def elongation_at(t):
        e = earth.at(t)
        s = e.observe(sun).apparent()
        cb = e.observe(curr_body).apparent()
        return s.separation_from(cb).degrees

    elongation_at.step_days = 15.0

    times, elongations = find_maxima(t0, t1, elongation_at)

    result = []

    for t, elongation_degrees in zip(times, elongations):
        e = earth.at(t)
        _, slon, _ = e.observe(sun).apparent().frame_latlon(ecliptic_frame)
        _, vlon, _ = e.observe(curr_body).apparent().frame_latlon(ecliptic_frame)
        is_east = (vlon.degrees - slon.degrees) % 360.0 < 180.0
        direction = 'east' if is_east else 'west'
        tz_t = t.astimezone(timezone)
        result.append({
            "year": t.utc.year,
            "month": t.utc.month,
            "day": t.utc.day,
            f"{l_body}_elong_time": tz_t,
            f"{l_body}_elong_degrees": elongation_degrees,
            f"{l_body}_elong_direction": direction
        })
    
    return result


def get_ephemeris_data(object: str, year: int, language: str) -> list[dict]:
    """
    Calculates the times of sunrise, transit and sunset of the sun
    or a planet for each day of the specified year. The data used
    comes from the position tables (de442s.bsp) published by JPL.

    Arguments:
      object (str): The object for which the ephemeris is calculated.
      year (int): Reference year.
      language (str): target language for position data. The language
                      is used to locate the observer's coordinates.
                      E.g.: “Italian” -> coordinates of Rome;
                      “French” -> coordinates of Paris

    Returns:
      list[dict]: daily list of dictionaries.
    """
    t = translator(language)
    timezone = ZoneInfo(t("timezone"))
    latitude = t("latitude")
    longitude = t("longitude")

    ts = load.timescale()
    eph = load(JPL_EPHEMERIS_FILE)
    bsp_object = bsp_alias(object, eph)
    target = eph[bsp_object.name]
    bluffton = wgs84.latlon(latitude, longitude)
    observer = eph["Earth"] + bluffton

    # Buffer of 10 days to ensure coverage during calendar generation
    start_date = datetime.date(year, 1, 1) - datetime.timedelta(days=10)
    end_date = datetime.date(year, 12, 31) + datetime.timedelta(days=10)
    delta = datetime.timedelta(days=1)

    results = []

    date = start_date
    while date <= end_date:
        # Calculate object events
        t0 = ts.utc(date.year, date.month, date.day, 0)
        t1 = ts.utc(date.year, date.month, date.day, 23, 59, 59)

        object_rise_times, _ = almanac.find_risings(
            observer, target, t0, t1
        )
        object_transit_times = almanac.find_transits(observer, target, t0, t1)
        object_set_times, are_sets_visibles = almanac.find_settings(
            observer, target, t0, t1
        )

        prefix = object.lower().split()[0]
        for ort, ott, ost, isvisible in zip(
            object_rise_times, object_transit_times,
            object_set_times, are_sets_visibles):  # pyright: ignore[reportArgumentType]
            time_ort = ort.astimezone(timezone)
            time_ott = ott.astimezone(timezone)
            time_ost = ost.astimezone(timezone)
            results.append(
                {
                    "year": date.year,
                    "month": date.month,
                    "day": date.day,
                    f"{prefix}_rise": time_ort,
                    f"{prefix}_transit": time_ott,
                    f"{prefix}_set": time_ost,
                    f"{prefix}_isvisible": isvisible,
                }
            )

        date += delta

    return results


def get_moon_phases(year):
    """
    Calculates all lunar phases for the specified year and adjacent years.

    Args:
      year (int): Reference year.

    Returns:
      list: Sorted list of dictionaries containing:
            'year', 'month', 'day', 'phase_time', 'phase'.
    """
    phases = []

    # Ephem functions for lunar phases
    phase_functions = {
        "new": ephem.next_new_moon,
        "firstquarter": ephem.next_first_quarter_moon,
        "full": ephem.next_full_moon,
        "lastquarter": ephem.next_last_quarter_moon,
    }

    # Process previous, current, and next year for edge cases
    for target_year in [year - 1, year, year + 1]:
        start_date = datetime.datetime(target_year, 1, 1)
        end_date = datetime.datetime(target_year, 12, 31, 23, 59, 59)

        for phase_name, next_phase_func in phase_functions.items():
            # Start slightly before the year to capture all initial phases
            current_date = start_date - datetime.timedelta(days=30)

            while True:
                next_phase = next_phase_func(current_date)
                phase_datetime = ephem.Date(next_phase).datetime()

                if phase_datetime > end_date:
                    break

                if start_date <= phase_datetime <= end_date:
                    phases.append(
                        {
                            "year": phase_datetime.year,
                            "month": phase_datetime.month,
                            "day": phase_datetime.day,
                            "phase_time": phase_datetime,
                            "phase": phase_name,
                        }
                    )

                # Advance by 1 day to find the subsequent phase of the same type
                current_date = phase_datetime + datetime.timedelta(days=1)

    # Chronological sort
    phases.sort(key=lambda x: (x["year"], x["month"], x["day"]))

    return phases


def get_easter_day(year):
    """
    Calculates the date of Easter Sunday using the Meeus/Jones/Butcher algorithm.

    This algorithm is valid for years in the Gregorian calendar (1583 onwards).
    Easter is defined as the first Sunday after the first full moon occurring
    on or after the spring equinox.

    Args:
      year (int): Year for calculation (must be >= 1583).

    Returns:
      dict: Dictionary containing:
            'year', 'month', 'day', and 'iseaster' flag.

    Raises:
      ValueError: If the year is before the introduction of the Gregorian calendar.
    """
    if year < 1583:
        raise ValueError("[get_easter_day]: The year must be >= 1583 (Gregorian Calendar).")

    # Meeus/Jones/Butcher Algorithm
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1

    return {"year": year, "month": month, "day": day, "iseaster": True}


def get_mooneclipses_data(year: int, timezone: str) -> list[dict]:
    """
    Calculates lunar eclipse data for a given year and timezone.

    This function searches for lunar eclipses starting from December of the previous
    year through January of the following year to ensure all eclipses relevant to
    the requested year (accounting for timezone shifts) are captured.

    Args:
      year (int): The calendar year for which to retrieve eclipse data (e.g., 2026).
      timezone (str): A valid IANA timezone string (e.g., 'Europe/Rome', 'UTC').

    Returns:
      list[dict]: A list of dictionaries, where each dictionary contains:
        - year (int): The year of the eclipse in the local timezone.
        - month (int): The month of the eclipse.
        - day (int): The day of the eclipse.
        - time (datetime.time): The specific time of the eclipse (rounded to the minute).
        - ecl_type_num (int): The numeric code representing the eclipse type.
        - ecl_type_descr (str): The human-readable description of the eclipse type
          (e.g., 'Total', 'Partial', 'Penumbral').

    Example:
      >>> get_mooneclipses_data(2026, "America/New_York")
      [{'year': 2026, 'month': 3, 'day': 3, 'time': datetime.time(6, 34), ...}]
    """
    ts = load.timescale()
    eph = load(JPL_EPHEMERIS_FILE)
    t0 = ts.utc(year - 1, 12, 1)
    t1 = ts.utc(year + 1, 1, 31)
    t, y, _ = eclipselib.lunar_eclipses(t0, t1, eph)

    results = []
    for ti, yi in zip(t, y):
        eclipse_datetime = ti.astimezone(ZoneInfo(timezone))
        results.append(
            {
                "year": eclipse_datetime.year,
                "month": eclipse_datetime.month,
                "day": eclipse_datetime.day,
                "time": eclipse_datetime.time(),
                "ecl_type_num": yi,
                "ecl_type_descr": eclipselib.LUNAR_ECLIPSES[yi],
            }
        )

    return results


def get_seasons(year):
    """
    Calculates the dates for equinoxes and solstices for the specified year.

    Args:
      year (int): Reference year.

    Returns:
      list[dict]: List of seasonal events containing:
                  'year', 'month', 'day', 'event_ord' (0: Spring, 1: Summer, 2: Autumn, 3: Winter).
    """
    result = []

    # Iterates through the four cardinal points of the year
    for i in range(4):
        if i == 0:
            # Spring Equinox
            data = ephem.next_equinox(f"{year-1}/12/21")
        elif i == 1:
            # Summer Solstice
            data = ephem.next_solstice(f"{year}/03/20")
        elif i == 2:
            # Autumn Equinox
            data = ephem.next_equinox(f"{year}/06/21")
        else:
            # Winter Solstice
            data = ephem.next_solstice(f"{year}/09/22")

        if data.datetime().year == year:
            result.append(
                {
                    "year": data.datetime().year,
                    "month": data.datetime().month,
                    "day": data.datetime().day,
                    "event_ord": i,
                }
            )

    return result
