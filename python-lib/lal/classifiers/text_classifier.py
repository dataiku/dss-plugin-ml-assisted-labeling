import json
import logging

import pandas as pd
import copy as cp
import re

TEXT_COLUMN_DEFAULT_LABEL = 'text'

from lal.classifiers.base_classifier import TableBasedDataClassifier


class TextClassifier(TableBasedDataClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self, initial_df, queries_df, config=None):
        self.__initial_df = initial_df
        self.text_column = config.get("text_column")
        self.token_sep = ' '  # config.get("token_sep")
        self.historical_labels = {}
        super(TextClassifier, self).__init__(queries_df, config)

    def get_initial_df(self):
        return self.__initial_df

    def clean_data_to_save(self, lab):
        return {
            'text': lab['text'],
            'start': lab['start'],
            'end': lab['end'],
            'label': lab['label'],
            'tokenStart': lab['tokenStart'],
            'tokenEnd': lab['tokenEnd']
        }

    def get_relevant_config(self):
        return {
            "textColumn": self.text_column,
            "tokenSep": self.token_sep
        }

    def format_for_saving(self, label):
        cleaned_labels = [self.clean_data_to_save(lab) for lab in label]
        return self.serialize_label(cleaned_labels)

    def serialize_label(self, label):
        return json.dumps(label)

    def deserialize_label(self, label):
        return json.loads(label)

    def add_prelabels(self, batch, user_meta):
        history = self.build_history_from_meta(user_meta)
        for item in batch:
            item['prelabels'] = self.find_prelabels(history, item["data"]["raw"][self.text_column])

    def build_history_from_meta(self, user_meta):
        history = {}
        for meta in user_meta:
            for lab in self.deserialize_label(meta["label"]):
                txt = lab["text"].lower()
                if txt in history and lab["label"] == history[txt]["label"]:
                    history[txt]["cpt"] += 1
                else:
                    history[txt] = {
                        "label": lab["label"],
                        "cpt": 1
                    }
        return history

    def find_prelabels(self, history, text):
        prelabels = []
        if not history:
            return prelabels
        regexp = '\\b({})\\b'.format('|'.join(list(history.keys())))
        for match in re.finditer(regexp, text, re.IGNORECASE):
            prelabels.append({
                "text": match.group(),
                "label": history[match.group().lower()]['label'],
                "start": match.start(),
                "end": match.end()
            })
        prelabels.sort(key=(lambda x: x["start"]))
        full_prelabels = self.insert_token_indexes(prelabels, text)
        return full_prelabels

    def insert_token_indexes(self, prelabels, text):
        nprelabels = cp.deepcopy(prelabels)
        separator_iter = re.finditer(self.token_sep, text + ' ')
        token_index = 0
        cont = True
        if self.token_sep not in text:
            if nprelabels:
                nprelabels[0]["tokenStart"] = token_index
                nprelabels[0]["tokenEnd"] = token_index
            return nprelabels
        for plab in nprelabels:
            while cont:
                try:
                    cur_sep = next(separator_iter)
                except StopIteration:
                    cont = False
                print('---------------- start -----------------')
                print(nprelabels)
                print(text)
                print(plab)
                print(cur_sep)
                print('---------------- end -----------------')
                if cur_sep.start() >= plab["start"] and "tokenStart" not in plab:
                    plab["tokenStart"] = token_index
                if cur_sep.start() >= plab["end"]:
                    plab["tokenEnd"] = token_index
                    break
                token_index += 1
        return nprelabels

    @property
    def type(self):
        return 'text'

    @property
    def is_dynamic(self):
        return True

    @staticmethod
    def format_labels_for_stats(raw_labels_series):
        labels = []
        for v in raw_labels_series.values:
            if pd.notnull(v):
                labels += [a['label'] for a in json.loads(v) if a['label']]
        return pd.Series(labels)
