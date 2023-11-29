import pandas as pd
from datetime import datetime


class DataService:

    def __init__(self, table_name_2_table):
        self.table_name_2_table = table_name_2_table

    def get_data_subset(self, table_name, begin_date, end_date, user_ids=None, columns=None):
        df = self.table_name_2_table[table_name]        
        if begin_date:
            df = df[df['date'] >= begin_date]           
        if end_date:
            df = df[df['date'] < end_date]        
        if user_ids:
            df = df[df['user_id'].isin(user_ids)]            
        if columns:
            df = df[columns]           
        return df.copy()