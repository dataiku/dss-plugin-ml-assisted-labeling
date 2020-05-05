import hashlib
import json
import logging
from abc import abstractmethod
from datetime import datetime
from typing import TypeVar

import pandas as pd

from lal.classifiers.base_classifier import BaseClassifier

META_STATUS_LABELED = 'LABELED'

META_STATUS_SKIPPED = 'SKIPPED'

BATCH_SIZE = 20

C = TypeVar('C', bound=BaseClassifier)


class LALHandler(object):
    logger = logging.getLogger(__name__)

    def __init__(self, classifier, label_col_name, meta_df, labels_df, user, do_users_share_labels=True):
        """
        :type classifier: C
        """
        self.classifier = classifier
        self.lbl_col = label_col_name
        self.lbl_id_col = label_col_name + "_id"
        self._skipped = {}
        self.meta_df = meta_df.set_index("date", drop=False)
        self.labels_df = labels_df
        self.current_user = user
        self.do_users_share_labels = do_users_share_labels

    def get_meta_by_status(self, status=None):
        if self.do_users_share_labels:
            return self.meta_df if status is None else self.meta_df[self.meta_df.status == status]
        else:
            if status is None:
                return self.meta_df[self.meta_df.annotator == self.current_user]
            return self.meta_df[
                (self.meta_df.status == status) & (self.meta_df.annotator == self.current_user)]

    def get_remaining(self):
        seen_ids = set(self.get_meta_by_status().data_id.values)
        logging.info("get_remaining: Seen ids: {0}".format(seen_ids))
        return [i for i in self.classifier.get_all_item_ids_list() if i not in seen_ids]

    def calculate_stats(self):
        total_count = len(self.classifier.get_all_item_ids_list())
        stats = {
            "labeled": len(self.get_meta_by_status(META_STATUS_LABELED)),
            "total": total_count,
            "skipped": len(self.get_meta_by_status(META_STATUS_SKIPPED)),
            "perLabel": self.get_meta_by_status(META_STATUS_LABELED)[self.lbl_col].astype(
                'str').value_counts().to_dict()
        }
        return stats

    def get_config(self):
        result = {"al_enabled": self.classifier.is_al_enabled}
        custom_config = self.classifier.get_config()
        if custom_config is not None:
            result = {**result, **custom_config}
        return result

    def label(self, data):
        self.logger.info("Labeling: %s" % json.dumps(data))
        if 'id' not in data:
            message = "Labeling data doesn't contain sample ID"
            self.logger.error(message)
            raise ValueError(message)

        data_id = data.get('id')
        lbl_id = self.create_label_id(data_id)
        raw_data = self.classifier.get_raw_item_by_id(data_id)

        serialized_label = self.classifier.serialize_label(data.get('label'))
        label = {**raw_data, **{self.lbl_col: serialized_label, self.lbl_id_col: lbl_id}}
        meta = {
            self.lbl_col: serialized_label,
            self.lbl_id_col: lbl_id,
            'date': datetime.now(),
            'data_id': data_id,
            'status': META_STATUS_LABELED,
            'comment': data.get('comment'),
            'session': self.classifier.get_session(),
            'annotator': self.current_user,
        }
        self.meta_df = self.meta_df[self.meta_df[self.lbl_id_col] != lbl_id]
        self.meta_df = self.meta_df.append(meta, ignore_index=True)

        self.labels_df = self.labels_df[self.labels_df[self.lbl_id_col] != lbl_id]
        self.labels_df = self.labels_df.append(label, ignore_index=True)

        self.save_item_label(self.labels_df, label)
        self.save_item_meta(self.meta_df, meta)
        return {
            "label_id": lbl_id,
            "stats": self.calculate_stats()
        }

    def create_label_id(self, data_id):
        return hashlib.md5(''.join([str(data_id), self.current_user]).encode('utf-8')).hexdigest()

    def is_stopping_criteria_met(self):
        return len(self.get_remaining()) < 0

    def get_batch(self):
        self.logger.info("Getting unlabeled batch")
        stats = self.calculate_stats()
        self.logger.info("Stats: {0}".format(stats))
        if self.is_stopping_criteria_met():
            return {"isDone": True, "stats": stats}

        remaining = self.get_remaining()
        ids_batch = remaining[-BATCH_SIZE:]
        ids_batch.reverse()
        return {
            "type": self.classifier.type,
            "items": [{"id": data_id, "data": self.classifier.get_item_by_id(data_id)} for data_id in ids_batch],
            "isLastBatch": len(remaining) < BATCH_SIZE,
            "stats": stats
        }

    def current_user_meta(self):
        return self.meta_df[(self.meta_df.annotator == self.current_user)]

    def first(self):
        return self.create_annotation_response(self.current_user_meta().iloc[0],
                                               is_first=True,
                                               is_last=len(self.current_user_meta()) == 1)

    def next(self, current_data_id):
        if not current_data_id:
            raise ValueError("Empty annotation id")

        self.logger.info(f"Going forward from {current_data_id}")
        meta = self.current_user_meta()

        current_data_meta = meta[meta['data_id'] == current_data_id]
        if not len(current_data_meta):
            raise ValueError(f"Couldn't find annotation with ID: {current_data_id}")

        next_els = meta[meta.date > current_data_meta.iloc[0].date]

        return self.create_annotation_response(next_els.iloc[0], is_first=False, is_last=len(next_els) == 1)

    def previous(self, current_data_id):
        is_first = False
        is_last = False
        self.logger.info(f"Going back from {current_data_id}")
        user_meta = self.current_user_meta()

        current_data_meta = user_meta[user_meta['data_id'] == current_data_id]
        if len(current_data_meta):
            previous = user_meta[user_meta.date < current_data_meta.iloc[0].date]
            is_first = len(previous) == 1
            if not len(previous):
                raise ValueError("Reached the first labeled annotation")
            previous = previous.iloc[len(previous) - 1]
        else:
            is_last = True
            is_first = len(user_meta) == 1
            previous = user_meta.iloc[len(user_meta) - 1]
        return self.create_annotation_response(previous, is_first=is_first, is_last=is_last)

    def create_annotation_response(self, annotation, is_first, is_last):
        annotation = annotation.where((pd.notnull(annotation)), None).astype('object').to_dict()
        data_id = annotation['data_id']
        if annotation['status'] != META_STATUS_SKIPPED:
            label = self.classifier.deserialize_label(annotation[self.lbl_col])
        else:
            label = None
        return {
            "annotation": {"label": label, "comment": annotation['comment']},
            "isFirst": is_first,
            "isLast": is_last,
            "item": {"id": data_id,
                     "labelId": annotation[self.lbl_id_col],
                     "data": self.classifier.get_item_by_id(data_id)}
        }

    def skip(self, data):
        data_id = data.get('dataId')
        label_id = data.get('labelId')
        lbl_id = self.create_label_id(data_id)
        meta = {
            'date': datetime.now(),
            'data_id': data_id,
            'status': META_STATUS_SKIPPED,
            self.lbl_col: None,
            self.lbl_id_col: lbl_id,
            'comment': data.get('comment'),
            'session': self.classifier.get_session(),
            'annotator': self.current_user,
        }
        self.meta_df = self.meta_df[self.meta_df[self.lbl_id_col] != lbl_id]
        self.meta_df = self.meta_df.append(meta, ignore_index=True)

        if label_id:
            self.labels_df = self.labels_df[self.labels_df[self.lbl_id_col] != lbl_id]

        self.save_item_meta(self.meta_df, meta)
        self.save_item_label(self.labels_df)
        return {"label_id": lbl_id, "stats": self.calculate_stats()}

    @abstractmethod
    def save_item_label(self, new_label_df, new_label=None):
        pass

    @abstractmethod
    def save_item_meta(self, new_meta_df, new_meta=None):
        pass
