import dataiku
from dataiku.customtrigger import *
from dataiku.scenario import Trigger


trigger_config = get_trigger_config()

t = Trigger()

labeling_count = int(trigger_config['i_labeling_count'])
metadata_df = dataiku.Dataset(trigger_config['ds_metadata']).get_dataframe()
queries_df = dataiku.Dataset(trigger_config['ds_queries']).get_dataframe()

trigger = False

# Metadata dataset contains labels corresponding to the last sessions labeled.
# Queries dataset contains queries corresponding to the next sessions to label.
next_session = queries_df['session'].max()
n_labeling = (metadata_df['session'] == next_session).sum()
trigger = (n_labeling >= labeling_count)

if trigger:
    t.fire()