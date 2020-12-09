# -*- coding: utf-8 -*-
"""Module with constants defining the language support of underlying NLP libraries"""

SUPPORTED_LANGUAGES_SPACY = {
    "af": "Afrikaans",
    "ar": "Arabic",
    "bg": "Bulgarian",
    "bn": "Bengali",
    "ca": "Catalan",
    "cs": "Czech",
    "da": "Danish",
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "et": "Estonian",
    "eu": "Basque",
    "fa": "Persian",
    "fi": "Finnish",
    "fr": "French",
    "ga": "Irish",
    "gu": "Gujarati",
    "he": "Hebrew",
    "hi": "Hindi",
    "hr": "Croatian",
    "hu": "Hungarian",
    "hy": "Armenian",
    "id": "Indonesian",
    "is": "Icelandic",
    "it": "Italian",
    "kn": "Kannada",
    "lb": "Luxembourgish",
    "lt": "Lithuanian",
    "lv": "Latvian",
    "mk": "Macedonian",
    "ml": "Malayalam",
    "mr": "Marathi",
    "nb": "Norwegian Bokmål",
    "ne": "Nepali",
    "nl": "Dutch",
    "pl": "Polish",
    "pt": "Portuguese",
    "ro": "Romanian",
    "ru": "Russian",
    "sa": "Sanskrit",
    "si": "Sinhala",
    "sk": "Slovak",
    "sl": "Slovenian",
    "sq": "Albanian",
    "sr": "Serbian",
    "sv": "Swedish",
    "ta": "Tamil",
    "te": "Telugu",
    "th": "Thai",
    "tl": "Tagalog",
    "tr": "Turkish",
    "tt": "Tatar",
    "uk": "Ukrainian",
    "ur": "Urdu",
    "vi": "Vietnamese",
    "yo": "Yoruba",
    "zh": "Chinese (simplified)",
}
"""dict: Languages supported by spaCy: https://spacy.io/usage/models#languages

Dictionary with ISO 639-1 language code (key) and language name (value)
Japanese and Korean were excluded for now because of system installation issues
"""

UNSUPPORTED_SPACY_EMOJI_LANG = ['th', 'zh']
"""list: Unsupported languages for spacymoji"""

SPACY_LANGUAGE_MODELS = {
    "en": "en_core_web_sm",  # OntoNotes
    "es": "es_core_news_sm",  # Wikipedia
    "zh": "zh_core_web_sm",  # OntoNotes
    "xx": "xx_ent_wiki_sm",  # Wikipedia
    "pl": "nb_core_news_sm",  # NorNE
    "fr": "fr_core_news_sm",  # Wikipedia
    "de": "de_core_news_sm",  # OntoNotes
}
"""dict: Mapping between ISO 639-1 language code and spaCy model identifiers

Models with Creative Commons licenses are not included because this plugin is licensed under Apache-2
"""
