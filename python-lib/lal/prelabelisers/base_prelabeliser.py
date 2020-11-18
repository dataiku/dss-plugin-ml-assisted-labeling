import pandas as pd

class BasePrelabeliser:
    def __init__(self, meta_df):
        self.meta_df = meta_df
