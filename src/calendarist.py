# -*- coding: utf-8 -*-
"""
Calendar data generation and processing module.
Handles the creation of daily date structures, localization of names,
and merging of astronomical data (moon phases, sun times, seasons)
with holidays and religious dates.
"""

import datetime
import scribus  # pyright: ignore[reportMissingImports]
from . import astronomer
from .data.localization import translator, by_acronym
from .data.holidays import holidays
from .utilities import generate_filename


def generate_dates(anno: int) -> list[dict]:
    """
    Generates a list of dictionaries containing information for each day of the
    specified year, extending the range to start from the preceding Monday
    and end with the following Sunday to complete the weeks.

    Args:
      anno (int): The year for which to generate the list.

    Returns:
      list[dict]: A list of daily dictionaries with keys:
                  'id', 'year', 'month', 'day', 'weekday'.
    """
    # Start and end dates of the target year
    primo_gennaio = datetime.date(anno, 1, 1)
    ultimo_dicembre = datetime.date(anno, 12, 31)

    # Find the first Monday on or before January 1st
    giorni_prima = primo_gennaio.weekday()  # Monday=0, Sunday=6
    data_inizio = primo_gennaio - datetime.timedelta(days=giorni_prima)

    # Find the first Sunday on or after December 31st
    giorni_dopo = 6 - ultimo_dicembre.weekday()
    data_fine = ultimo_dicembre + datetime.timedelta(days=giorni_dopo)

    # Populate the date list
    delta = data_fine - data_inizio
    giorni = []
    index = 1
    for i in range(delta.days + 1):
        giorno_corrente = data_inizio + datetime.timedelta(days=i)
        giorni.append(
            {
                "id": index,
                "year": giorno_corrente.year,
                "month": giorno_corrente.month,
                "day": giorno_corrente.day,
                "weekday": giorno_corrente.weekday(),
            }
        )
        index += 1

    return giorni


def add_translation(date_list: list[dict], language: str) -> list[dict]:
    """
    Appends translated month and weekday names to each date entry.

    Args:
      date_list (list[dict]): The list of daily data dictionaries.
      language (str): The target language (e.g., "English", "Italian").

    Returns:
      list[dict]: A new list with 'translated_month' and 'translated_weekday' added.

    Raises:
      ValueError: If the language is not found in the localization data.
      IndexError: If month or weekday indices are out of expected bounds.
    """
    t = translator(language)
    months = t("months")
    weekdays = t("weekdays")

    translated_list = []
    for d in date_list:
        # month_index is 0-based for list access (input month is 1-12)
        month_index = d["month"] - 1
        weekday_index = d["weekday"]

        if not (0 <= month_index < len(months)):
            raise IndexError(f"Invalid month index: {month_index}")
        if not (0 <= weekday_index < len(weekdays)):
            raise IndexError(f"Invalid weekday index: {weekday_index}")

        new_entry = d.copy()
        new_entry["translated_month"] = months[month_index]
        new_entry["translated_weekday"] = weekdays[weekday_index]
        translated_list.append(new_entry)

    return translated_list


def translated_seasons(seasons: list[dict], language: str) -> list[dict]:
    """
    Translates season names (Equinoxes/Solstices) based on the target language.

    Args:
      seasons (list[dict]): List of seasonal events from the astronomer module.
      language (str): Target language for translation.

    Returns:
      list[dict]: Season data with 'translated_season' key.
    """
    t = translator(language)
    season_strs = t("seasons")

    result = []
    for d in seasons:
        event_index = d["event_ord"]

        if not (0 <= event_index < len(season_strs)):
            raise IndexError(f"Invalid season event index: {event_index}")

        new_entry = d.copy()
        new_entry["translated_season"] = season_strs[event_index]
        result.append(new_entry)

    return result


def get_holidays_list(year: int, language: str) -> list[dict]:
    """
    Retrieves the list of fixed holidays for a given year.

    Args:
      year (int): The target year.
      language (str): The target language for holiday names.

    Returns:
      list[dict]: List of holiday dictionaries with 'month', 'day', and 'name'.
    """
    holidays_for_year = []
    for holiday in holidays:
        holidays_for_year.append(
            {
                "year": year,
                "month": holiday["month"],
                "day": holiday["day"],
                "holiday_name": holiday["name"][language],
            }
        )
    return holidays_for_year


def merge_calendar_data(target_list, **data_sources):
    """
    Merges several lists of astronomical and calendar data into a main target list.

    Args:
      target_list (list): The main list of dictionaries containing dates (year, month, day).
      **data_sources: Optional data lists passed as keyword arguments (e.g., sun_data_list=...).
                      Supported keys include:
                      - moon_phases_list, moon_eclipses_list
                      - sun_data_list, moon_data_list
                      - mercury_data_list, venus_data_list, mars_data_list
                      - jupiter_data_list, saturn_data_list
                      - easter_data_list, holidays_list, seasons_list

    Returns:
      list: A new list with dictionaries from target_list enriched with the merged data.
    """

    # 1. Configuration: Defines how to handle each data source.
    # 'key_type': 'ymd' (Year-Month-Day) or 'md' (Month-Day for recurring holidays).
    # 'mapping': Dictionary {source_key: dest_key}. If None, copies identical keys.
    # 'fields': List of fields to copy directly (alternative to 'mapping' for 1:1 copies).

    # Standard configuration for planets (direct copy of specific fields)
    input_lists = [
        "fixed_holidays_list",
        "seasons_list",
        "sun_data_list",
        "moon_data_list",
        "mercury_data_list",
        "venus_data_list",
        "mars_data_list",
        "jupiter_data_list",
        "saturn_data_list",
    ]

    config = {
        "moon_phases_list": {"key_type": "ymd", "fields": ["phase", "phase_time"]},
        "moon_eclipses_list": {
            "key_type": "ymd",
            "mapping": {
                "time": "moon_eclipse_time",
                "ecl_type_num": "moon_eclipse_type_num",
                "ecl_type_descr": "moon_eclipse_type_descr",
            },
        },
        "easter_data_list": {
            "key_type": "ymd",
            "mapping": {"holiday_name": "holiday_name"},
        },
        "fixed_holidays_list": {
            "key_type": "md",  # Short key
            "mapping": {"holiday_name": "holiday_name"},
        },
        "seasons_list": {
            "key_type": "ymd",
            "mapping": {
                "translated_season": "season",
                "event_ord": "season_type"
            }
        },
    }

    # Add planets to configuration (generic logic: copy everything found)
    for p_list in input_lists:
        if p_list not in config:
            config[p_list] = {"key_type": "ymd", "auto_merge": True}

    # 2. Pre-processing: Convert all input lists into optimized lookup dictionaries
    lookups = {}

    for source_name, source_list in data_sources.items():
        if source_name not in config:
            continue  # Ignore unrecognized or unconfigured arguments

        cfg = config[source_name]
        lookup_dict = {}

        for item in source_list:
            # Generate lookup key
            m = int(item["month"])
            d = int(item["day"])
            if cfg["key_type"] == "md":
                key = (m, d)
            else:
                y = int(item["year"])
                key = (y, m, d)
            lookup_dict[key] = item

        lookups[source_name] = lookup_dict

    # 3. Merging: Iterate over target_list and merge data
    result = []

    for target_item in target_list:
        merged_item = target_item.copy()

        # Pre-calculate keys for this item
        ty = int(target_item["year"])
        tm = int(target_item["month"])
        td = int(target_item["day"])

        full_key = (ty, tm, td)
        short_key = (tm, td)

        for source_name, lookup_dict in lookups.items():
            cfg = config[source_name]

            # Select the correct key to use
            current_key = short_key if cfg["key_type"] == "md" else full_key

            if current_key in lookup_dict:
                source_data = lookup_dict[current_key]

                # Case A: Explicit mapping (rename fields: source -> dest)
                if "mapping" in cfg:
                    for src_key, dest_key in cfg["mapping"].items():
                        if src_key in source_data:
                            merged_item[dest_key] = source_data[src_key]

                # Case B: Explicit field list (copy fields: key -> key)
                elif "fields" in cfg:
                    for field in cfg["fields"]:
                        if field in source_data:
                            merged_item[field] = source_data[field]

                # Case C: Auto merge (for planets, copy specific planet fields)
                elif cfg.get("auto_merge"):
                    # Copy all keys that are not year/month/day
                    for k, v in source_data.items():
                        if k not in ("year", "month", "day"):
                            merged_item[k] = v

        result.append(merged_item)

    return result


def notify(progess_index: int, message: str):
    t = translator(by_acronym(scribus.getGuiLanguage()))
    scribus.progressSet(progess_index)
    scribus.statusMessage(t(message))


def print_as_json(data, filename):
    """
    Writes a list of dictionaries to a text file in a JSON-like format.

    This function iterates through a list of dictionaries and formats them
    manually into a string representation. It ensures that there are no
    trailing commas after the last item in each dictionary or after the
    last dictionary in the list, maintaining valid syntax.

    Args:
      data (list[dict]): A list of dictionaries to be written to the file.
      filename (str): The name or path of the file to be created or overwritten.

    Returns:
      None
    """
    with open(filename, "w") as f:
        f.write("[\n")

        num_dicts = len(data)
        for i, d in enumerate(data):
            f.write("  {\n")

            # Convert dictionary items to a list of formatted strings
            items = [f'    "{key}": "{value}"' for key, value in d.items()]

            # Join items with a comma and newline, ensuring no trailing comma
            f.write(",\n".join(items))
            f.write("\n  }")

            # Add a comma after the closing brace unless it is the last dictionary
            if i < num_dicts - 1:
                f.write(",")
            f.write("\n")

        f.write("]\n")


def generate_full_calendar(year: int, language: str) -> list[dict]:
    """
    High-level function to generate a complete calendar with all features.

    Coordinates date generation, localization, astronomical calculations
    via the astronomer module, and data merging.

    Args:
      year (int): Target year.
      language (str): Target language for UI/Labels.

    Returns:
      list[dict]: The final calendar dataset ready for rendering.
    """
    t = translator(language)

    # Generate core date structures
    scribus.progressTotal(10)
    scribus.progressReset()
    notify(1, "cal_structure_creation")
    base_dates = generate_dates(year)

    # Localization
    translated_dates = add_translation(base_dates, language)

    # Fetch data from astronomical module
    notify(2, "cal_sun_eph")
    sun_data = astronomer.get_ephemeris_data("Sun", year, language)

    notify(3, "cal_moon_eph")
    moon_data = astronomer.get_ephemeris_data("Moon", year, language)
    moon_phases = astronomer.get_moon_phases(year)
    easter_day = astronomer.get_easter_day(year)
    moon_eclipses = astronomer.get_mooneclipses_data(year, t("timezone"))

    # Prepare Easter and Easter Monday
    easter_data = [
        {
            "year": easter_day["year"],
            "month": easter_day["month"],
            "day": easter_day["day"],
            "holiday_name": t("holidays")[0],
        },
        {
            "year": easter_day["year"],
            "month": easter_day["month"],
            "day": easter_day["day"] + 1,
            "holiday_name": t("holidays")[1],
        },
    ]

    notify(4, "cal_mercury_eph")
    mercury_data = astronomer.get_ephemeris_data("Mercury", year, language)

    notify(5, "cal_venus_eph")
    venus_data = astronomer.get_ephemeris_data("Venus", year, language)

    notify(6, "cal_mars_eph")
    mars_data = astronomer.get_ephemeris_data("Mars barycenter", year, language)

    notify(7, "cal_jupiter_eph")
    jupiter_data = astronomer.get_ephemeris_data("Jupiter barycenter", year, language)

    notify(8, "cal_saturn_eph")
    saturn_data = astronomer.get_ephemeris_data("Saturn barycenter", year, language)

    notify(9, "cal_equinoxes_eph")
    fixed_holidays = get_holidays_list(year, language)
    seasons = translated_seasons(astronomer.get_seasons(year), language)

    # Consolidate all data into final list
    full_calendar = merge_calendar_data(
        translated_dates,
        moon_data_list=moon_data,
        moon_phases_list=moon_phases,
        moon_eclipses_list=moon_eclipses,
        sun_data_list=sun_data,
        easter_data_list=easter_data,
        fixed_holidays_list=fixed_holidays,
        seasons_list=seasons,
        mercury_data_list=mercury_data,
        venus_data_list=venus_data,
        mars_data_list=mars_data,
        jupiter_data_list=jupiter_data,
        saturn_data_list=saturn_data,
    )

    #--temp
    calendar_filename = generate_filename(prefix='calendar_', ext='.json')
    print_as_json(full_calendar, calendar_filename)
    #--remove before release--/

    scribus.progressReset()
    scribus.statusMessage("")

    return full_calendar
