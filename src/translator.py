from .data.localization import languages


def by_acronym(target_acronym: str) -> str:
    """
    Searches for a language name based on its acronym.

    Args:
      target_acronym (str): The acronym to look for (e.g., 'it', 'fr').

    Returns:
      str: The name of the language (the dictionary key) if found,
           otherwise 'Italian' as the default value.
    """
    # Iterate through the language names and their respective data dictionaries
    for lang_name, lang_data in languages.items():
        # Check if the 'acronym' key exists and matches the target
        if lang_data.get("acronym") == target_acronym[:2]:
            return lang_name

    # Default return value if no match is found
    return "Italian"


def translator(language: str):
    """
    A factory function that creates a localized lookup utility.

    This function determines the best available language match from a global
    'languages' dictionary and returns a specialized 'result' function.
    If the requested language is not found, it defaults to 'Italian'.

    Args:
      language (str): The name of the language to use for translations
                      (e.g., 'English', 'Spanish').

    Returns:
      function: The 'result' function, configured for the chosen language.
    """
    # Fallback to 'Italian' if the requested language is not available
    lang = language if language in languages else "Italian"

    def result(translation_key: str) -> str:
        """
        Retrieves the translated string for a given key.

        This function accesses the specific language dictionary selected by
        the parent 'translator' function. It is designed to be safe: if
        a key is missing, it returns an empty string instead of raising
        a KeyError.

        Args:
          translation_key (str): The unique identifier for the string
                                 (e.g., 'checkform_title').

        Returns:
          str: The localized text if the key exists; otherwise, an empty string.
        """
        return languages[lang].get(translation_key, "")

    return result
