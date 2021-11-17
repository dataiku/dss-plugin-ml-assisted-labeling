# -*- coding: utf-8 -*-
# This is a test file intended to be used with pytest
# pytest automatically runs all the function starting with "test_"
# see https://docs.pytest.org for more information
import json
import pytest
from ml_assisted_labeling_to_computer_vision.object_detection import format_labeling_plugin_annotations


def test_format_labeling_plugin_annotations():
    correct_labeling_annotations = json.dumps([
        {"top": 283, "left": 218, "width": 189, "height": 108, "label": "fish"},
        {"top": 560, "left": 367, "width": 295, "height": 102, "label": "fish"}
    ])

    expected_output = json.dumps([
        {"bbox": [218, 283, 189, 108], "category": "fish"},
        {"bbox": [367, 560, 295, 102], "category": "fish"}
    ])

    output = format_labeling_plugin_annotations(correct_labeling_annotations)
    assert isinstance(output, str)
    assert output == expected_output

def test_format_labeling_plugin_annotations__img_skipped():
    skipped_labeling_annotations = float("nan")
    expected_output = json.dumps([])

    output = format_labeling_plugin_annotations(skipped_labeling_annotations)
    assert isinstance(output, str)
    assert output == expected_output

def test_format_labeling_plugin_annotations__wrong_format():
    for skipped_labeling_annotations in ("toto", ""):
        with pytest.raises(Exception):
            format_labeling_plugin_annotations(skipped_labeling_annotations)
