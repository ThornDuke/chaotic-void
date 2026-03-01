# -*- coding: utf-8 -*-
from pathlib import Path
import json
import os


def translator(language):
    """Configures a translator for a specific language.

    This function attempts to find the translation file by matching the input
    with the 'meta.language' or 'meta.acronym' fields in any JSON file within
    the './intl' directory.

    Args:
        language (str): The language name or acronym (e.g., 'English', 'en').

    Returns:
        callable: A `search(key_path)` function that returns the translated string
            or the original `key_path` if no match is found or the key is missing.
    """
    directory_path = "./intl"
    json_data = {}
    exists = False

    # Check if directory exists
    if not os.path.isdir(directory_path):
        print(f"|  ERR: The directory '{directory_path}' does not exist.")
    else:
        # Search for the correct file by scanning the directory
        target_file = None
        for filename in os.listdir(directory_path):
            if filename.endswith(".json"):
                path = os.path.join(directory_path, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        meta = data.get("meta", {})

                        # Check if input matches acronym or full language name
                        if language.lower() in [
                            str(meta.get("acronym", "")).lower(),
                            str(meta.get("language", "")).lower(),
                        ]:
                            target_file = path
                            json_data = data
                            exists = True
                            break
                except (json.JSONDecodeError, OSError):
                    continue

        if not exists:
            print(f"|  ERR: No translation file found for language '{language}'.")

    def search(key_path):
        """Retrieves a translation from the loaded JSON data.

        Args:
            key_path (str): The path to the key within the JSON file (dot notation).

        Returns:
            str: The translated string if found; otherwise, returns the `key_path`.
        """
        if not exists:
            return key_path

        keys = key_path.split(".")
        current_value = json_data

        for key in keys:
            if isinstance(current_value, dict) and key in current_value:
                current_value = current_value[key]
            else:
                print(f"|  ERR: Cannot find key '{key}' in path '{key_path}'.")
                return key_path

        if isinstance(current_value, str):
            return current_value
        else:
            print(f"|  ERR: The value in '{key_path}' is not a string.")
            return key_path

    return search


def init():
    """
    Creates the 'intl' directory and initializes it with a default 'en.json' file.

    The JSON file includes metadata for the English language, such as its
    full name and acronym.
    """
    # Define the directory and file paths
    directory = Path("intl")
    file_path = directory / "en.json"

    # Create the directory if it doesn't exist
    # exist_ok=True prevents errors if the folder is already there
    directory.mkdir(exist_ok=True)

    # Define the content for en.json
    en_content = {"meta": {"language": "English", "acronym": "en"}}

    try:
        # Write the dictionary to the file as JSON
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(en_content, f, indent=2)
        print(f"|  SUCCESS: Created {file_path} successfully.")
    except OSError as e:
        print(f"|  ERR: Could not create the translation file: {e}")


def file_init(language, acronym):
    """
    Creates a JSON translation file inside the 'intl' directory.

    The file is named after the acronym (e.g., 'it.json') and contains
    the language metadata. If the 'intl' directory is missing, the
    function prints an error and aborts.

    Args:
        language (str): The full name of the language (e.g., 'Italiano').
        acronym (str): The language code (e.g., 'it').
    """
    directory = Path("intl")
    file_path = directory / f"{acronym}.json"

    # Check if the directory exists
    if not directory.is_dir():
        print(f"|  ERR: The directory '{directory}' does not exist. Aborting.")
        return

    # Prepare the JSON structure
    content = {"meta": {"language": language, "acronym": acronym}}

    try:
        # Write the file with UTF-8 encoding and indentation for readability
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(content, f, indent=2, ensure_ascii=False)
        print(f"|  SUCCESS: Created '{file_path}' successfully.")
    except OSError as e:
        print(f"|  ERR: Could not create file '{file_path}': {e}")
