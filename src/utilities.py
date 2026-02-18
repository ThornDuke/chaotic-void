# -*- coding: utf-8 -*-
import re
import datetime
import sys
import pprint
import importlib.metadata
import scribus  # pyright: ignore[reportMissingImports]
from .translator import by_acronym, translator

t_ui = translator(by_acronym(scribus.getGuiLanguage()))


def template_replace(template, **replacements):
    """
    Replaces placeholders in the format {{key_name}} with corresponding values
    provided as keyword arguments.

    Args:
      template (str): The string containing placeholders like {{example}}.
      **replacements: Arbitrary keyword arguments where the key matches
                      the placeholder name.

    Returns:
      str: The modified string with values substituted.

    Raises:
      KeyError: If a placeholder found in the template is missing from
                the provided keyword arguments.

    Example:
      >>> replace_placeholders_by_key("The {{item}} costs {{price}}", item="ball", price=10)
      'The ball costs 10'
    """

    def substitute(match):
        # match.group(1) captures the content inside {{ }}
        key = match.group(1).strip()
        if key not in replacements:
            raise KeyError(
                f"[template_replace]: Placeholder '{{{{{key}}}}}' not found in provided arguments."
            )
        return str(replacements[key])

    # Pattern: search for {{, then capture anything non-greedy until }}
    pattern = r"\{\{(.*?)\}\}"

    return re.sub(pattern, substitute, template)


def round_dt_to_min(dt):
    """
    Rounds a datetime object to the nearest minute.
    If the seconds are >= 30, round up, otherwise round down.
    """
    # 1. Create a new datetime by truncating the seconds and microseconds
    dt_truncated = dt.replace(second=0, microsecond=0)

    # 2. If the original seconds are 30 or more, add a minute
    if dt.second >= 30:
        return dt_truncated + datetime.timedelta(minutes=1)

    return dt_truncated


def check_requirements():
    """
    Checks the system environment against a set of predefined requirements
    necessary for the program to run within Scribus.

    It verifies:
    1. The running Scribus version.
    2. The Python interpreter version.
    3. Tkinter availability and version.
    4. Availability and version of specific Python libraries (ephem, skyfield).
    5. Availability of specific font families in Scribus.

    Returns:
      dict: A dictionary containing the status of all checks.
            Structure example:
            {
              'scribus': {'req_ver': (1, 6, 1), 'curr_ver': (1, 6, 2), 'is_enough': True},
              'tkinter': {'available': True, ...},
              'fonts': [{'FontName': True}, ...]
            }
    """

    def tk_available():
        try:
            import tkinter
        except ImportError:
            return False
        return True

    def lib_availability(lib_name, min_version):
        # 'packaging' is a third-party library. Use fallback if missing.
        try:
            from packaging.version import parse as parse_version # pyright: ignore[reportMissingImports]
        except ImportError:
            return {"available": False, "error": t_ui("checkform_lib_err")}

        try:
            curr_ver = importlib.metadata.version(lib_name)
            enough = parse_version(curr_ver) >= parse_version(min_version)
            return {
                "available": True,
                "req_ver": min_version,
                "curr_ver": curr_ver,
                "is_enough": enough,
            }
        except importlib.metadata.PackageNotFoundError:
            return {
                "available": False,
            }

    def font_availability(font_names):
        # scribus.getFontNames() returns a list of installed fonts
        font_list = scribus.getFontNames()
        return [{fn: fn in font_list} for fn in font_names]


    # --- Requirements ---
    SCRIBUSV = (1, 6, 1)
    PYTHONV = (3, 12, 3)
    TKV = 8.6
    LIBRARIES = {"ephem": "4.1.5", "skyfield": "1.48"}
    FONTS = [
        "Simoncini Garamond Std Bold",
        "Simoncini Garamond Std Italic",
        "Simoncini Garamond Std Roman",
        "Symbola Regular",
        "AstroGadget Regular"
    ]

    report = {}

    # --- Scribus Version ---
    scribus_req_ver = SCRIBUSV
    # scribus_version_info is usually longer (e.g., 1.6.1.svn), take first 3
    scribus_curr_ver = scribus.scribus_version_info[:3]
    scribus_is_enough = scribus_curr_ver >= scribus_req_ver
    report["scribus"] = {
        "req_ver": scribus_req_ver,
        "curr_ver": scribus_curr_ver,
        "is_enough": scribus_is_enough,
    }

    # --- Python Version ---
    python_req_ver = PYTHONV
    python_curr_ver = sys.version_info
    # sys.version_info compares correctly with tuples
    python_is_enough = python_curr_ver >= python_req_ver
    report["python"] = {
        "req_ver": python_req_ver,
        "curr_ver": python_curr_ver,  # Stores the full sys.version_info object
        "is_enough": python_is_enough,
    }

    # --- Tkinter Version ---
    has_tkinter = tk_available()
    if has_tkinter:
        import tkinter

        tkinter_req_ver = TKV
        tkinter_curr_ver = tkinter.TkVersion
        tkinter_is_enough = tkinter_curr_ver >= tkinter_req_ver
        report["tkinter"] = {
            "available": has_tkinter,
            "req_ver": tkinter_req_ver,
            "curr_ver": tkinter_curr_ver,
            "is_enough": tkinter_is_enough,
        }
    else:
        report["tkinter"] = {
            "available": False,
        }

    # --- Libraries ---
    report["libraries"] = {}
    for lib, lib_ver in LIBRARIES.items():
        report["libraries"][lib] = lib_availability(lib, lib_ver)

    # --- Fonts ---
    report["fonts"] = font_availability(FONTS)

    #--temp / debug
    # with open('report.txt', 'w') as rf:
    #   for item in report:
    #     rf.write(f"{item}: {report[item]}\n")
    #--remove before release--/

    return report


def validate_requirements(report):
    """
    Analyzes the report generated by check_requirements() and alerts the user
    if any dependencies are missing or outdated.

    If issues are found, it compiles a readable error message and displays it
    using scribus.messageBox().

    Args:
      report (dict): The dictionary output from check_requirements().

    Returns:
      bool: True if all requirements are met, False if anything is missing.
    """
    missing_items = []

    # 1. Check Scribus
    if not report["scribus"]["is_enough"]:
        req = ".".join(map(str, report["scribus"]["req_ver"]))
        curr = ".".join(map(str, report["scribus"]["curr_ver"]))
        missing_items.append(
            template_replace(t_ui("checkform_scribus"), curr_ver=curr, req_ver=req)
        )

    # 2. Check Python
    if not report["python"]["is_enough"]:
        req = ".".join(map(str, report["python"]["req_ver"]))
        # Extract major.minor.micro from sys.version_info
        v = report["python"]["curr_ver"]
        curr = f"{v.major}.{v.minor}.{v.micro}"
        missing_items.append(
            template_replace(t_ui("checkform_python"), curr_ver=curr, req_ver=req)
        )

    # 3. Check Tkinter
    tk_rep = report["tkinter"]
    if not tk_rep["available"]:
        missing_items.append(t_ui("chekform_tk"))
    elif not tk_rep["is_enough"]:
        missing_items.append(
            template_replace(
                t_ui("checkform_tk_ver"),
                curr_ver=tk_rep["curr_ver"],
                req_ver=tk_rep["req_ver"],
            )
        )

    # 4. Check Libraries (generic handler for ephem, skyfield, etc.)
    for lib in report["libraries"].keys():
        lib_rep = report["libraries"].get(lib)
        if not lib_rep:
            continue

        if "error" in lib_rep:
            missing_items.append(
                template_replace(
                    "• {{lib_name}}: {{err}}", lib_name=lib, err=lib_rep["error"]
                )
            )

        elif not lib_rep["available"]:
            missing_items.append(template_replace(t_ui("checkform_lib"), library=lib))
        elif not lib_rep["is_enough"]:
            missing_items.append(
                template_replace(
                    t_ui("checkform_lib_ver"),
                    library=lib,
                    curr_ver=lib_rep["curr_ver"],
                    req_ver=lib_rep["req_ver"],
                )
            )

    # 5. Check Fonts
    # fonts report structure is [{'FontName': True/False}, ...]
    for font_entry in report["fonts"]:
        for font_name, exists in font_entry.items():
            if not exists:
                missing_items.append(
                    template_replace(t_ui("checkform_font"), font_name=font_name)
                )

    # Final Decision
    if missing_items:
        error_msg = f"{t_ui('checkform_msg_warn')}\n\n"
        error_msg += "\n".join(missing_items)
        error_msg += f"\n\n{t_ui('checkform_msg_tip')}"

        scribus.messageBox(
            f"{t_ui('checkform_title')}", error_msg, scribus.ICON_CRITICAL
        )
        return False

    return True

def generate_filename(prefix='', suffix='', ext=''):
    """
    Generate a timestamped filename string.

    Args:
        prefix (str): Text to prepend to the filename.
        suffix (str): Text to append after the timestamp.
        ext (str): File extension including the dot (e.g., '.pdf').

    Returns:
        str: A formatted filename containing the current date and time.
    """
    now = datetime.datetime.now()
    timestamp = now.strftime('%y%m%dT%H%M%S')
    return f"{prefix}{timestamp}{suffix}{ext}"

def save_to_file(data, filename):
    formatted_data = pprint.pformat(data, sort_dicts=False)
    with open(filename, 'w') as f:
        f.write(formatted_data)
        f.close()