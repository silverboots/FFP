import pandas as pd

def style_alternating_rows(df: pd.DataFrame):
    """Apply alternating row colors to a dataframe."""
    def highlight_rows(row):
        if row.name % 2 == 0:
            return ["background-color: #f8f9fa"] * len(row)
        return ["background-color: #ffffff"] * len(row)
    return df.style.apply(highlight_rows, axis=1)