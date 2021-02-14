"""Prepare data for Plotly Dash."""
import numpy as np
import pandas as pd
from ..app import db

def create_dataframe():
    """Create Pandas DataFrame from local CSV."""
    df_tables = pd.read_sql("SELECT table_name FROM information_schema.tables WHERE table_schema='public'",
        con=db.engine,
        parse_dates=[
            'created_on'
        ]
    )

    d = {'id': [0], 'created_on': ['2021-02-01 00:00:00'], 'sesion_id': ['0'], 'user': ['demo@dataplate.io'],
         'kind': ['demo'], 'text':['']}
    if df_tables.empty:
        df = pd.DataFrame(data=d,index=['id'])
        # df.to_sql(name='audit_entries',con=db.engine)
        return df
    else:
        if 'audit_entries' not in df_tables.to_numpy():
            df = pd.DataFrame(data=d,index=['id'])
            return df
            # df.to_sql(name='audit_entries', con=db.engine)

    df = pd.read_sql(
        "SELECT * FROM audit_entries order by created_on desc",
        con=db.engine,
        parse_dates=[
            'created_on'
        ]
    )
    df.set_index('id', inplace=True, drop=False)
    if '_fts' in df.columns:
        df.drop(columns=["_fts"], inplace=True)
    #id, created_on, session_id, "user", kind, "text", "_fts" FROM public.audit_entries;

    return df
