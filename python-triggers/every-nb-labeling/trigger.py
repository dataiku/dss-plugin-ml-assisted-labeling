import logging

import dataiku
from dataiku.customtrigger import *
from dataiku.scenario import Trigger

from lal import utils
logging.basicConfig(level=logging.INFO, format='%(name)s %(levelname)s - %(message)s')

logger = logging.getLogger("EveryNLabelingTrigger")
trigger_config = get_trigger_config()

t = Trigger()

labeling_count = int(trigger_config['i_labeling_count'])
metadata_df = dataiku.Dataset(trigger_config['ds_metadata']).get_dataframe()
queries_df = dataiku.Dataset(trigger_config['ds_queries']).get_dataframe()

trigger = False

# Metadata dataset contains labels corresponding to the last sessions labeled.
# Queries dataset contains queries corresponding to the next sessions to label.
if queries_df.empty:
    trigger = metadata_df['session'].shape[0] > labeling_count
else:

    next_session = utils.get_current_session_id(trigger_config['ds_queries'])
    n_labeling = (metadata_df['session'] == next_session).sum()
    trigger = (n_labeling >= labeling_count)
    logger.info(
        f"next_session: {next_session}; n_labeling: {n_labeling}; trigger: {trigger}; labeling_count: {labeling_count}")


if trigger:
    t.fire()
