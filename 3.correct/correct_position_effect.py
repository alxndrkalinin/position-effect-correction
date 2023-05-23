from typing import Optional

import pandas as pd

from scipy.stats import median_abs_deviation
from statsmodels.formula.api import ols

from tqdm.auto import tqdm


def subtract_well_mean(ann_df: pd.DataFrame) -> pd.DataFrame:
    '''Subtract the mean of each feature per each well.
    
    Parameters
    ----------
    ann_df : pandas.DataFrame
        Dataframe with features and metadata.
    
    Returns
    -------
    pandas.DataFrame
        Dataframe with features and metadata, with each feature subtracted by the mean of that feature per well.
    '''
    feature_cols = ann_df.filter(regex="^(?!Metadata_)").columns
    ann_df[feature_cols] = ann_df.groupby("Metadata_Well")[feature_cols].transform(lambda x: x - x.mean())
    return ann_df


def mad_robustize_col(col: pd.Series, epsilon: float = 0.0):
    """
    Robustize a column by median absolute deviation.
    
    Parameters
    ----------
    col : pandas.core.series.Series
        Column to robustize.
    epsilon : float, default 0.0
        Epsilon value to add to denominator.

    Returns
    -------
    col : pandas.core.series.Series
        Robustized column.
    """
    col_mad = median_abs_deviation(col, nan_policy="omit", scale=1/1.4826)
    return (col - col.median()) / (col_mad + epsilon)


def regress_out_cell_counts(ann_df: pd.DataFrame, cc_col: str, min_unique: int = 100, cc_rename: Optional[str] = None, inplace: bool = True) -> pd.DataFrame:
    """
    Regress out cell counts from all features in a dataframe.

    Parameters
    ----------
    ann_df : pandas.core.frame.DataFrame
        DataFrame of annotated profiles.
    cc_col : str
        Name of column containing cell counts.
    min_unique : int, optional
        Minimum number of unique feature values to perform regression.
    cc_rename : str, optional
        Name to rename cell count column to.
    inplace : bool, optional
        Whether to perform operation in place.

    Returns
    -------
    df : pandas.core.frame.DataFrame
    """
    df = ann_df if inplace else ann_df.copy()

    feature_cols = df.filter(regex="^(?!Metadata_)").columns.to_list()
    feature_cols.remove(cc_col)

    for feature in tqdm(feature_cols):
        if df[feature].nunique() > min_unique:
            model = ols(f"{feature} ~ {cc_col}", data=df).fit()
            df[f"{feature}"] = model.resid

    if cc_rename is not None:
        df.rename(columns={cc_col: cc_rename}, inplace=True)
    return df