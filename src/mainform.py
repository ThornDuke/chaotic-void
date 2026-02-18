# -*- coding: utf-8 -*-
"""
Main GUI module for the Scribus Planner script.
This module handles the user interface for selecting the calendar year
and the target language using the Tkinter library.
"""

from scribus import getGuiLanguage  # pyright: ignore[reportMissingImports]
import tkinter as tk
from tkinter import ttk
from datetime import datetime
from .translator import translator, by_acronym
from .data.localization import languages

# --- Global Variables ---

# Used for aesthetic window positioning based on the divine proportion
GOLDEN_RATIO = 1.61803

# List of available language keys imported from the localization data
languages_list = sorted(list(languages.keys()))

t_ui = translator(by_acronym(getGuiLanguage()))


def get_planner_edition():
    """
    Displays a modal dialog with comboboxes for year and language selection.

    The window is automatically centered on the screen using the Golden Ratio
    for vertical positioning.

    Returns:
      dict: A dictionary containing 'year' (int) and 'language' (str) if the user clicks OK.
      None: If the user clicks Cancel or closes the window.
    """
    result = None

    def on_ok():
        """Handles the OK button click: stores values and closes the UI."""
        nonlocal result
        result = {"year": int(year_var.get()), "language": language_var.get()}
        root.destroy()

    def on_cancel():
        """Handles the Cancel button click or window closure."""
        nonlocal result
        result = None
        root.destroy()

    # Main window initialization
    root = tk.Tk()
    root.title(t_ui("mainform_title"))
    root.resizable(False, False)

    # Main container frame with padding
    main_frame = ttk.Frame(root, padding="10")
    main_frame.grid(row=0, column=0, sticky=tk.W)

    # Year selection logic (current year +/- 25 years)
    current_year = datetime.now().year
    years = list(range(current_year - 25, current_year + 26))

    # Year Label and Combobox
    ttk.Label(main_frame, text=f"{t_ui('mainform_year')}:").grid(
        row=0, column=0, sticky=tk.W, pady=5
    )
    year_var = tk.StringVar(value=str(current_year))
    year_combo = ttk.Combobox(
        main_frame,
        textvariable=year_var,
        values=[str(year) for year in years],
        state="readonly",
        width=20,
    )
    year_combo.grid(row=0, column=1, pady=5, padx=(10, 0))

    # Language Label and Combobox
    ttk.Label(main_frame, text=f"{t_ui('mainform_language')}:").grid(
        row=1, column=0, sticky=tk.W, pady=5
    )
    language_var = tk.StringVar(value="English")
    language_combo = ttk.Combobox(
        main_frame,
        textvariable=language_var,
        values=languages_list,
        state="readonly",
        width=20,
    )
    language_combo.grid(row=1, column=1, pady=5, padx=(10, 0))

    # Visual separator
    separator = ttk.Separator(main_frame, orient=tk.HORIZONTAL)
    separator.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=15)

    # Button container
    button_frame = ttk.Frame(main_frame)
    button_frame.grid(row=3, column=0, columnspan=2, pady=5)

    # OK and Cancel buttons
    ok_button = ttk.Button(
        button_frame, text=f"{t_ui('btn_ok')}", command=on_ok, width=10
    )
    ok_button.grid(row=0, column=0, padx=5)

    cancel_button = ttk.Button(
        button_frame, text=f"{t_ui('btn_cancel')}", command=on_cancel, width=10
    )
    cancel_button.grid(row=0, column=1, padx=5)

    # Handle window 'X' close button
    root.protocol("WM_DELETE_WINDOW", on_cancel)

    # Center the window on screen
    root.update_idletasks()
    x = int((root.winfo_screenwidth() / 2) - (root.winfo_width() / 2))
    y = int(
        root.winfo_screenheight()
        - (root.winfo_screenheight() / GOLDEN_RATIO)
        - (root.winfo_height() / GOLDEN_RATIO)
    )
    root.geometry(f"+{x}+{y}")

    # Start the GUI event loop
    root.mainloop()

    return result
