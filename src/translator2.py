# -*- coding: utf-8 -*-
import json
import os


def translator(language):
    """
    Creates a translation function for a specific language based on a JSON file.

    This factory function checks for the existence of the translation directory
    and the specific language file. It returns a 'parse' function that can
    retrieve nested strings from the loaded JSON using dot-notation keys.

    Args:
        language (str): The language code (e.g., 'en', 'it') which corresponds
            to the filename (e.g., 'en.json').

    Returns:
        callable: A function that takes a dot-notation string key and returns
            the corresponding translated string.

    Raises:
        FileNotFoundError: If the './intl/' directory or the '{language}.json'
            file does not exist.
    """
    directory_path = "./intl"
    file_path = os.path.join(directory_path, f"{language}.json")

    # Check if the directory exists
    if not os.path.isdir(directory_path):
        raise FileNotFoundError(
            f"[translator] The directory '{directory_path}' was not found."
        )

    # Check if the translation file exists
    if not os.path.isfile(file_path):
        raise FileNotFoundError(
            f"[translator] The translation file '{file_path}' does not exist."
        )

    with open(file_path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)

    def parse(key_path):
        """
        Retrieves a string value from the loaded JSON data using a dotted path.

        Args:
            key_path (str): Dotted path representing the keys (e.g., 'home.title').

        Returns:
            str: The string value found at the specified path.

        Raises:
            ValueError: If the value found is not a string.
            KeyError: If the path does not exist within the dictionary.
        """
        keys = key_path.split(".")
        current_value = json_data

        try:
            for key in keys:
                current_value = current_value[key]

            if isinstance(current_value, str):
                return current_value
            else:
                raise ValueError(
                    f"[translator] The value found for '{key_path}' is not a string."
                )

        except (KeyError, TypeError):
            raise KeyError(
                f"[translator] Path '{key_path}' not found in the dictionary."
            )

    return parse
