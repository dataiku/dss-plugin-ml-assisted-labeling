import json
import logging

import pandas as pd
import re
import emoji
from lal.tokenizers.spacy_tokenizer import MultilingualTokenizer
from lal.tokenizers.language_dict import SUPPORTED_LANGUAGES_SPACY


from lal.classifiers.base_classifier import TableBasedDataClassifier


class TextClassifier(TableBasedDataClassifier):
    logger = logging.getLogger(__name__)
    WHITESPACE_TOKEN_ENGINE = 'white_space'
    CHARACTER_TOKEN_ENGINE = 'char'

    LANGUAGE_COLUMN_PARAM = 'language_column'
    NO_LANGUAGE_PARAM = 'none'

    CLASSIC_PRELABEL_ENGINE = 'classic'

    def __init__(self, initial_df, queries_df, config=None):
        self.__initial_df = initial_df
        self.use_tokenization = True
        self.tokenizer = self.use_tokenization and MultilingualTokenizer()
        self.text_column = config.get("text_column")
        self.language = config.get("language")
        self.language_column = config.get("language_column")
        self.token_engine = config.get("tokenization_engine")
        self.text_direction = config.get("text_direction")
        self.token_sep = self.get_token_sep()
        self.historical_labels = {}
        super(TextClassifier, self).__init__(queries_df, config)

    def get_token_sep(self):
        if self.token_engine == self.WHITESPACE_TOKEN_ENGINE:
            return ' '
        elif self.token_engine == self.CHARACTER_TOKEN_ENGINE:
            return ''
        else:
            return ' '

    def get_initial_df(self):
        return self.__initial_df

    def serialize_label(self, label):
        cleaned_labels = [self.clean_data_to_save(lab) for lab in label]
        return json.dumps(cleaned_labels)

    def add_prelabels(self, batch, user_meta):
        if self.prelabeling_strategy == self.CLASSIC_PRELABEL_ENGINE:
            self.classic_prelabeling(batch, user_meta)

    def classic_prelabeling(self, batch, user_meta):
        history = self.build_history_from_meta(user_meta)
        for item in batch:
            item['prelabels'] = self.find_prelabels(history, item["data"]["raw"]["tokenized_text"])

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

    def find_prelabels(self, history, tokenized_text):
        text = tokenized_text["text"]
        prelabels = []
        if not history:
            return prelabels
        regexp = '({})'.format('|'.join(list(history.keys())))
        regexp = ('\\b{}\\b' if self.token_engine == self.WHITESPACE_TOKEN_ENGINE else '{}').format(regexp)
        emojis = list(re.finditer(emoji.get_emoji_regexp(), text))
        for match in re.finditer(regexp, text, re.IGNORECASE):
            pl_start = match.start() - sum([x.end() - x.start() - 1 for x in emojis if x.end() <= match.start()])
            pl_end = match.end() - sum([x.end() - x.start() - 1 for x in emojis if x.end() <= match.end()])
            if self.is_legit_prelabel(pl_start, pl_end, tokenized_text["tokens"]):
                prelabels.append({
                    "text": match.group(),
                    "label": history[match.group().lower()]['label'],
                    "start": pl_start,
                    "end": pl_end
                })
        prelabels.sort(key=(lambda x: x["start"]))
        self.logger.debug(f"Prelabels : {prelabels}")
        return prelabels

    def is_legit_prelabel(self, pl_start, pl_end, tokens):
        return any([t for t in tokens if t["start"] == pl_start]) and any([t for t in tokens if t["end"] == pl_end])

    def get_raw_item_by_id(self, data_id):
        raw_item = super(TextClassifier, self).get_raw_item_by_id(data_id)
        if self.tokenizer:
            tokenized_text = self.tokenize_text(raw_item)
            raw_item['tokenized_text'] = tokenized_text
        return raw_item

    def tokenize_text(self, raw_item):
        text = raw_item.get(self.text_column)
        language = raw_item[self.language_column] if self.language == self.LANGUAGE_COLUMN_PARAM else self.language
        if not language in list(SUPPORTED_LANGUAGES_SPACY.keys()) + ['none']:
            self.logger.error("The language {} does not belong to supported languages. Applying English".format(language))
            language = 'en'
        if language == self.NO_LANGUAGE_PARAM:
            doc_dict = self.dummy_tokenization(text)
        else:
            doc_dict = self.spacy_tokenization(text, language)
        return doc_dict

    def spacy_tokenization(self, text, language):
        spacy_doc = self.tokenizer.tokenize_list(
            text_list=[text],
            language=language
        )[0]
        doc_dict = spacy_doc.to_json()
        doc_dict['writingSystem'] = spacy_doc.vocab.writing_system
        for tk in doc_dict['tokens']:
            tk['whitespace'] = spacy_doc[tk['id']].whitespace_
            tk['text'] = spacy_doc[tk['id']].text
        return doc_dict

    def tokenization_by_pattern(self, text, pattern):
        tokens = []
        tokens_it = re.finditer(r"{emoji_pattern}|{pattern}".format(
            emoji_pattern=emoji.get_emoji_regexp().pattern,
            pattern=pattern
        ), text, re.UNICODE)
        current = next(tokens_it)
        i = 0
        while current:
            try:
                nxt = next(tokens_it)
            except StopIteration:
                nxt = None
            tokens.append({
                "start": current.start(),
                "end": current.end(),
                "text": current.group(),
                "whitespace": text[current.end():nxt.start()] if nxt else "",
                "id": i
            })
            current = nxt
            i += 1
        return tokens

    def dummy_tokenization(self, text):
        dummy_doc = {
            "text": text,
            "writingSystem": {
                "direction": self.text_direction
            }
        }
        if self.token_engine == self.CHARACTER_TOKEN_ENGINE:
            dummy_doc["tokens"] = self.tokenization_by_pattern(text, r".")
        elif self.token_engine == self.WHITESPACE_TOKEN_ENGINE:
            dummy_doc["tokens"] = self.tokenization_by_pattern(text, r"\w+|[^\w\s]")
        return dummy_doc

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
            'label': lab['label']
        }

    @staticmethod
    def format_labels_for_stats(raw_labels_series):
        labels = []
        for v in raw_labels_series.values:
            if pd.notnull(v):
                labels += [a['label'] for a in json.loads(v) if a['label']]
        return pd.Series(labels)
