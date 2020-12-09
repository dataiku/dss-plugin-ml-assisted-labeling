import json
import logging

import pandas as pd
import re
import emoji
from lal.tokenizer.spacy_tokenizer import MultilingualTokenizer

WHITESPACE_TOKEN_ENGINE = 'white_space'
CHARACTER_TOKEN_ENGINE = 'char'

CLASSIC_PRELABEL_ENGINE = 'classic'

from lal.classifiers.base_classifier import TableBasedDataClassifier


class TextClassifier(TableBasedDataClassifier):
    logger = logging.getLogger(__name__)

    def __init__(self, initial_df, queries_df, config=None):
        self.__initial_df = initial_df
        self.use_tokenization = True
        self.tokenizer = self.use_tokenization and MultilingualTokenizer()
        self.language = 'en'
        self.text_column = config.get("text_column")
        self.token_engine = config.get("tokenization_engine")
        self.text_direction = config.get("text_direction")
        self.token_sep = self.get_token_sep()
        self.historical_labels = {}
        super(TextClassifier, self).__init__(queries_df, config)

    def get_token_sep(self):
        if self.token_engine == WHITESPACE_TOKEN_ENGINE:
            return ' '
        elif self.token_engine == CHARACTER_TOKEN_ENGINE:
            return ''
        else:
            return ' '

    def get_initial_df(self):
        return self.__initial_df

    def get_relevant_config(self):
        return {
            "text_column": self.text_column,
            "text_direction": self.text_direction,
            "token_sep": self.token_sep
        }

    def serialize_label(self, label):
        cleaned_labels = [self.clean_data_to_save(lab) for lab in label]
        return json.dumps(cleaned_labels)

    def add_prelabels(self, batch, user_meta):
        if self.prelabeling_strategy == CLASSIC_PRELABEL_ENGINE:
            self.classic_prelabeling(batch, user_meta)

    def classic_prelabeling(self, batch, user_meta):
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
        regexp = '({})'.format('|'.join(list(history.keys())))
        regexp = ('\\b{}\\b' if self.token_engine == WHITESPACE_TOKEN_ENGINE else '{}').format(regexp)
        emojis = list(re.finditer(emoji.get_emoji_regexp(), text))
        for match in re.finditer(regexp, text, re.IGNORECASE):
            prelabels.append({
                "text": match.group(),
                "label": history[match.group().lower()]['label'],
                "start": match.start() - sum([x.end() - x.start() - 1 for x in emojis if x.end() <= match.start()]),
                "end": match.end() - sum([x.end() - x.start() - 1 for x in emojis if x.end() <= match.end()])
            })
        prelabels.sort(key=(lambda x: x["start"]))
        self.logger.debug(f"Prelabels : {prelabels}")
        return prelabels

    def get_raw_item_by_id(self, data_id):
        raw_item = super(TextClassifier, self).get_raw_item_by_id(data_id)
        if self.tokenizer:
            tokenized_text = self.tokenize_text(raw_item.get(self.text_column))
            raw_item['tokenized_text'] = tokenized_text
        return raw_item

    def tokenize_text(self, text):
        spacy_doc = self.tokenizer.tokenize_list(text_list=[text], language=self.language)[0]
        doc_dict = spacy_doc.to_json()
        for tk in doc_dict['tokens']:
            tk['whitespace'] = spacy_doc[tk['id']].whitespace_
        return doc_dict

    @property
    def type(self):
        return 'text'

    @property
    def is_multi_label(self):
        return True

    @staticmethod
    def deserialize_label(label):
        return json.loads(label)

    @staticmethod
    def clean_data_to_save(lab):
        return {
            'text': lab['text'],
            'start': lab['start'],
            'end': lab['end'],
            'label': lab['label'],
            'tokenStart': lab['tokenStart'],
            'tokenEnd': lab['tokenEnd']
        }

    @staticmethod
    def format_labels_for_stats(raw_labels_series):
        labels = []
        for v in raw_labels_series.values:
            if pd.notnull(v):
                labels += [a['label'] for a in json.loads(v) if a['label']]
        return pd.Series(labels)
