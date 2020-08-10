import json
import logging
from abc import abstractmethod
from datetime import datetime, timedelta
from threading import RLock
from typing import TypeVar, Dict

import pandas as pd

from lal.classifiers.base_classifier import BaseClassifier
from lal.utils import get_local_categories

logging.basicConfig(level=logging.INFO, format='%(name)s %(levelname)s - %(message)s')

META_STATUS_LABELED = 'LABELED'
META_STATUS_SKIPPED = 'SKIPPED'

BLOCK_SAMPLE_BY_USER_FOR_MINUTES = 0.5
BATCH_SIZE = 20

C = TypeVar('C', bound=BaseClassifier)


class ReservedSample:
    username: str
    reserved_until: datetime

    def __init__(self, username: str, reserved_until: datetime) -> None:
        self.username = username
        self.reserved_until = reserved_until

    def __repr__(self) -> str:
        return f"User: {self.username}; Reserved until: {self.reserved_until}"


class LALHandler(object):
    """Manages the Labels and Metadata"""
    lock = RLock()
    sample_by_user_reservation: Dict[str, ReservedSample] = dict()

    logger = logging.getLogger(__name__)

    def __init__(self, classifier, label_col_name, meta_df, labels_df, do_users_share_labels=True):
        """
        :type classifier: C
        """
        self.classifier = classifier
        self.lbl_col = label_col_name
        self.lbl_id_col = label_col_name + "_id"
        self._skipped = {}
        self.meta_df = meta_df.set_index(self.lbl_id_col, drop=False)
        self.labels_df = labels_df
        self.do_users_share_labels = do_users_share_labels
        self.last_used_label_id = self.meta_df[self.lbl_id_col].max() if len(self.meta_df) else 0

    def get_meta_by_status(self, user, status=None):
        if self.do_users_share_labels:
            return self.meta_df if status is None else self.meta_df[self.meta_df.status == status]
        else:
            if status is None:
                return self.meta_df[self.meta_df.annotator == user]
            return self.meta_df[
                (self.meta_df.status == status) & (self.meta_df.annotator == user)]

    def get_remaining(self, user):
        labeled_ids = set(self.get_meta_by_status(user).data_id.values)
        unlabeled_ids = [item_id for item_id in self.classifier.get_all_item_ids_list() if item_id not in labeled_ids]
        result = []
        with LALHandler.lock:
            for i in unlabeled_ids:
                if i in self.sample_by_user_reservation:
                    reserved_sample = self.sample_by_user_reservation.get(i)
                    if reserved_sample.reserved_until <= datetime.now():
                        del self.sample_by_user_reservation[i]
                        result.append(i)
                    elif reserved_sample.username == user:
                        result.append(i)
                else:
                    result.append(i)
        return result

    def calculate_stats(self, user):
        total_count = len(self.classifier.get_all_item_ids_list())
        labeled_samples = self.get_meta_by_status(user, META_STATUS_LABELED)
        skipped_samples = self.get_meta_by_status(user, META_STATUS_SKIPPED)
        stats = {
            "labeled": len(labeled_samples),
            "total": total_count,
            "skipped": len(skipped_samples),
            "perLabel": self.classifier.format_labels_for_stats(labeled_samples[self.lbl_col]).astype(
                'str').value_counts().to_dict()
        }
        return stats

    def get_config(self):
        result = {"al_enabled": self.classifier.is_al_enabled}
        if self.classifier.is_al_enabled:
            result["halting_thr"] = sorted([self.classifier.halting_thr_low, self.classifier.halting_thr_high])
        result['local_categories'] = get_local_categories()
        return result

    def label(self, data, user):
        self.logger.info("Labeling: %s" % json.dumps(data))
        if 'id' not in data:
            message = "Labeling data doesn't contain sample ID"
            self.logger.error(message)
            raise ValueError(message)

        data_id = data.get('id')
        user_meta = self.user_meta(user)
        existing_meta_record = user_meta[user_meta.data_id == data_id]

        lbl_id = self.create_label_id() if existing_meta_record.empty else existing_meta_record.iloc[0][self.lbl_id_col]
        raw_data = self.classifier.get_raw_item_by_id(data_id)

        serialized_label = self.classifier.serialize_label(data.get('label')) if data.get('label') else None
        label = {**raw_data, **{self.lbl_col: serialized_label, self.lbl_id_col: lbl_id}}
        meta = {
            self.lbl_col: serialized_label,
            self.lbl_id_col: lbl_id,
            'date': datetime.now(),
            'data_id': data_id,
            'status': META_STATUS_LABELED,
            'comment': data.get('comment'),
            'session': self.classifier.get_session(),
            'annotator': user,
        }
        self.meta_df = self.meta_df[self.meta_df[self.lbl_id_col] != lbl_id]
        self.meta_df = self.meta_df.append(meta, ignore_index=True)

        self.labels_df = self.labels_df[self.labels_df[self.lbl_id_col] != lbl_id]
        self.labels_df = self.labels_df.append(label, ignore_index=True)

        self.save_item_label(self.labels_df, label)
        self.save_item_meta(self.meta_df, meta)
        return {
            "label_id": int(lbl_id),
            "stats": self.calculate_stats(user)
        }

    def create_label_id(self):
        self.last_used_label_id += 1
        return self.last_used_label_id

    def is_stopping_criteria_met(self, user):
        return len(self.get_remaining(user)) < 0

    def get_batch(self, user):
        self.logger.info("Getting unlabeled batch")
        stats = self.calculate_stats(user)
        self.logger.info("Stats: {0}".format(stats))
        if self.is_stopping_criteria_met(user):
            return {"isDone": True, "stats": stats, "config": self.get_config()}

        remaining = self.get_remaining(user)
        ids_batch = remaining[-BATCH_SIZE:]
        with LALHandler.lock:
            reserved_until = datetime.now() + timedelta(minutes=int(BATCH_SIZE * BLOCK_SAMPLE_BY_USER_FOR_MINUTES))
            for i in ids_batch:
                self.sample_by_user_reservation[i] = ReservedSample(user, reserved_until)
        ids_batch.reverse()
        return {
            "type": self.classifier.type,
            "items": [{"id": data_id, "data": self.classifier.get_item_by_id(data_id)} for data_id in ids_batch],
            "isLastBatch": len(remaining) < BATCH_SIZE,
            "stats": stats,
            "config": self.get_config()
        }

    def user_meta(self, user):
        return self.meta_df[self.meta_df.annotator == user]

    def first(self, user):
        return self.create_annotation_response(self.user_meta(user).sort_values(self.lbl_id_col).iloc[0],
                                               is_first=True,
                                               is_last=len(self.user_meta(user)) == 1)

    def next(self, label_id, user):
        if not label_id:
            raise ValueError("Empty annotation id")

        self.logger.info(f"Going forward from label id: {label_id}")
        meta = self.user_meta(user)

        next_els = meta[meta[self.lbl_id_col] > label_id].sort_values(self.lbl_id_col)
        return self.create_annotation_response(next_els.iloc[0], is_first=False, is_last=len(next_els) == 1)

    def previous(self, label_id, user):
        is_last = False
        self.logger.info(f"Going back from label id: {label_id}")
        user_meta = self.user_meta(user)
        if label_id:
            previous = user_meta[user_meta[self.lbl_id_col] < label_id]
            is_first = len(previous) == 1
            if not len(previous):
                raise ValueError("Reached the first labeled annotation")
            previous = previous.sort_values(self.lbl_id_col).iloc[len(previous) - 1]
        else:
            is_last = True
            is_first = len(user_meta) == 1
            previous = user_meta.sort_values(self.lbl_id_col).iloc[len(user_meta) - 1]
        return self.create_annotation_response(previous, is_first=is_first, is_last=is_last)

    def create_annotation_response(self, annotation, is_first, is_last):
        annotation = annotation.where((pd.notnull(annotation)), None).astype('object').to_dict()
        data_id = annotation['data_id']
        if annotation[self.lbl_col] is not None and annotation['status'] != META_STATUS_SKIPPED:
            label = self.classifier.deserialize_label(annotation[self.lbl_col])
        else:
            label = None
        return {
            "annotation": {"label": label, "comment": annotation['comment']},
            "isFirst": is_first,
            "isLast": is_last,
            "item": {"id": data_id,
                     "status": annotation['status'],
                     "labelId": int(annotation[self.lbl_id_col]),
                     "data": self.classifier.get_item_by_id(data_id)}
        }

    def skip(self, data, user):
        data_id = data.get('dataId')
        label_id = data.get('labelId')
        lbl_id = data.get('labelId', self.create_label_id())
        meta = {
            'date': datetime.now(),
            'data_id': data_id,
            'status': META_STATUS_SKIPPED,
            self.lbl_col: None,
            self.lbl_id_col: lbl_id,
            'comment': data.get('comment'),
            'session': self.classifier.get_session(),
            'annotator': user,
        }
        self.meta_df = self.meta_df[self.meta_df[self.lbl_id_col] != lbl_id]
        self.meta_df = self.meta_df.append(meta, ignore_index=True)

        if label_id:
            self.labels_df = self.labels_df[self.labels_df[self.lbl_id_col] != lbl_id]

        self.save_item_meta(self.meta_df, meta)
        self.save_item_label(self.labels_df)
        return {"label_id": int(lbl_id), "stats": self.calculate_stats(user)}

    @abstractmethod
    def save_item_label(self, new_label_df, new_label=None):
        pass

    @abstractmethod
    def save_item_meta(self, new_meta_df, new_meta=None):
        pass
