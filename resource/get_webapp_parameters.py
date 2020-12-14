# -*- coding: utf-8 -*-
from lal.tokenizers.language_dict import SUPPORTED_LANGUAGES_SPACY


def do(payload, config, plugin_config, inputs):
    choices = []
    if payload["parameterName"] == "language":
        choices = sorted(
            [{"value": k, "label": v} for k, v in SUPPORTED_LANGUAGES_SPACY.items()], key=lambda x: x.get("label")
        )
        choices.insert(0, {"label": "Custom...", "value": "none"})
        choices.insert(0, {"label": "Detected language column", "value": "language_column"})
    return {"choices": choices}