import re


def count_syllables_portuguese(word):
    """
    Count syllables in a Portuguese word.
    Matches sequences of vowels as syllables and handles nasal vowels.
    """
    vowels = "aeiouáéíóúâêôàèìòùãõ"
    nasal_vowels = ["ão", "õe", "ões", "ãe", "ães"]

    for nasal in nasal_vowels:
        word = word.replace(nasal, "V")

    pattern = f"[{vowels}]+"
    return len(re.findall(pattern, word.lower()))
