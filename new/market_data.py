import os
import requests
import pandas as pd
import numpy as np
import urllib3
import statsmodels.api as sm
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64
import logging
from typing import List, Optional, Dict, Tuple, Any
from itertools import combinations
import matplotlib
matplotlib.use('Agg')
from config import EIKON_APP_KEY
import eikon as ek

# Disable SSL warnings for unverified requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MarketDataAnalyzer:
    """
    A comprehensive class for fetching, processing, and analyzing market data.
    """

    def __init__(self, api_url, auth_token, instruments_config):
        # You may not need api_url/auth_token anymore
        self.instruments_config = instruments_config
        ek.set_app_key(EIKON_APP_KEY)

    def fetch_market_data(self, instruments, interval="1H", count=100):
        """
        Returns a single long DataFrame with columns: ['time','product','close'].
        """
        interval_map = {"1H": "hour", "1D": "daily"}
        interval = interval_map.get(interval, interval)

        rows = []
        for ric in instruments:
            try:
                df = ek.get_timeseries(
                    ric, interval=interval, count=count,
                    fields=['OPEN', 'HIGH', 'LOW', 'CLOSE', 'VOLUME']
                )
                if df is not None and not df.empty:
                    df = df.copy()
                    df.index = pd.to_datetime(df.index)
                    df['product'] = ric
                    df['time'] = df.index
                    # Normalize to 'close'
                    if 'CLOSE' in df.columns:
                        df.rename(columns={'CLOSE': 'close'}, inplace=True)
                    else:
                        # try case-insensitive fallback
                        close_col = next((c for c in df.columns if c.upper() == 'CLOSE'), None)
                        if close_col is not None:
                            df.rename(columns={close_col: 'close'}, inplace=True)
                        else:
                            # no close -> skip this ric
                            continue
                    rows.append(df[['time', 'product', 'close']])
            except Exception as e:
                logger.error(f"Error fetching data for {ric}: {e}")
        return pd.concat(rows, ignore_index=True) if rows else None

    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Pivot and clean market data -> wide frame indexed by time with one column per instrument.
        - Ensures datetime index
        - Forces numeric, coercing bad values to NaN
        - Drops duplicate timestamps (keep last)
        - Drops all-empty columns
        """
        try:
            if df is None or df.empty:
                return pd.DataFrame()

            # Normalize column names (case-insensitive)
            cols_lower = {c.lower(): c for c in df.columns}
            required = {'time', 'product', 'close'}
            if not required.issubset(set(cols_lower.keys())):
                logger.error("Preprocess: required columns missing; got %s", df.columns.tolist())
                return pd.DataFrame()

            # Standardize columns
            df = df.rename(columns={
                cols_lower['time']: 'time',
                cols_lower['product']: 'product',
                cols_lower['close']: 'close'
            }).copy()

            # Ensure proper dtypes
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            df = df.dropna(subset=['time'])
            # Coerce prices to numeric
            df['close'] = pd.to_numeric(df['close'], errors='coerce')

            # Deduplicate time/product
            df = df.drop_duplicates(subset=['time', 'product'], keep='last')

            # Pivot to wide
            wide = df.pivot(index='time', columns='product', values='close').sort_index()
            wide.index.name = 'time'

            # Drop exact duplicate timestamps if any slipped through
            wide = wide[~wide.index.duplicated(keep='last')]

            # Drop all-empty columns and coerce everything to float
            wide = wide.dropna(how='all', axis=1).astype(float)

            return wide
        except Exception as e:
            logger.error(f"Data Preprocessing Failed: {e}")
            return pd.DataFrame()

    def compute_hedge_ratios(
        self,
        df: pd.DataFrame,
        instruments_1: List[str],
        instruments_2: Optional[List[str]] = None,
        cross_compare: bool = True,
        lookback_periods: int = 5
    ) -> pd.DataFrame:
        """
        Compute hedge ratios, correlations, and strategy metrics.
        Robust to dtype/NaN issues.
        """
        if df is None or df.empty:
            return pd.DataFrame()

        # Force numeric for entire matrix; keep index as-is (timestamps)
        df = df.apply(pd.to_numeric, errors='coerce')
        # Drop columns that are entirely NaN
        df = df.dropna(axis=1, how='all')

        if instruments_2 is None:
            instruments_2 = instruments_1

        # Filter out any non-string or empty instruments
        instruments_1 = [inst for inst in instruments_1 if isinstance(inst, str) and inst]
        instruments_2 = [inst for inst in instruments_2 if isinstance(inst, str) and inst]

        # Generate instrument pairs
        if cross_compare:
            instrument_pairs = [
                (leg_1, leg_2) for leg_1 in instruments_1 for leg_2 in instruments_2 if leg_1 != leg_2
            ]
        else:
            if instruments_1 == instruments_2:
                instrument_pairs = list(combinations(instruments_1, 2))
            else:
                instrument_pairs = [(leg_1, leg_2) for leg_1 in instruments_1 for leg_2 in instruments_2]

        # Ensure all instrument_pairs are 2-tuples of strings
        instrument_pairs = [
            pair for pair in instrument_pairs
            if isinstance(pair, tuple) and len(pair) == 2 and all(isinstance(x, str) and x for x in pair)
        ]

        strategy_data = []
        time_series_data: Dict[str, list] = {}

        # Self-pairs
        for instrument in instruments_1:
            strategy_data.append({
                "Strategy": f"{instrument}/{instrument}",
                "Leg 1": instrument,
                "Leg 2": instrument,
                "Correlation Coeff": 1.0,
                "Z-Score": 0.0,
                "Z-Score Slope": 0.0,
                "Hedge Ratio": 1.0
            })

        def _finite(x) -> bool:
            try:
                return np.isfinite(float(x))
            except Exception:
                return False

        for pair in instrument_pairs:
            try:
                leg_1, leg_2 = pair
            except Exception as e:
                logger.error(f"Invalid instrument pair: {pair} ({e})")
                continue

            if leg_1 not in df.columns or leg_2 not in df.columns:
                continue

            # Prepare clean numeric data for the pair
            try:
                data = df[[leg_1, leg_2]].apply(pd.to_numeric, errors='coerce').dropna()
            except Exception as e:
                logger.error(f"Pair subset error for {leg_1}/{leg_2}: {e}")
                continue

            if len(data) < max(lookback_periods + 1, 10):  # require minimal depth
                continue

            # Correlation
            try:
                arr1 = data[leg_1].astype(float).values
                arr2 = data[leg_2].astype(float).values
                std1 = np.std(arr1)
                std2 = np.std(arr2)
                if std1 == 0 or std2 == 0 or not np.isfinite(std1) or not np.isfinite(std2):
                    correlation_coef = 0.0
                else:
                    c = np.corrcoef(arr1, arr2)[0, 1]
                    correlation_coef = 0.0 if not np.isfinite(c) else float(c)
            except Exception as e:
                logger.error(f"Correlation error for {leg_1}/{leg_2}: {e}")
                correlation_coef = 0.0

            # OLS for hedge ratio
            try:
                x = data[leg_2].astype(float).values
                y = data[leg_1].astype(float).values
                X = sm.add_constant(x, has_constant='add')
                model = sm.OLS(y, X, missing='drop').fit()
                params = model.params
                beta = float(params[1]) if len(params) >= 2 else np.nan
            except Exception as e:
                logger.error(f"OLS error for {leg_1}/{leg_2}: {e}")
                beta = np.nan

            # Z-Score and slope
            try:
                if not np.isfinite(beta):
                    raise ValueError("beta is NaN/inf")

                spread = (data[leg_1].astype(float) - beta * data[leg_2].astype(float)).astype(float)
                spread_mean = float(spread.mean())
                spread_std = float(spread.std())

                if not np.isfinite(spread_std) or spread_std == 0.0:
                    z_scores = [0.0 for _ in range(-lookback_periods - 1, 0)]
                else:
                    z_scores = []
                    for i in range(-lookback_periods - 1, 0):
                        val = float(spread.iloc[i])
                        z = (val - spread_mean) / spread_std
                        z_scores.append(0.0 if not np.isfinite(z) else float(z))

                z_score = z_scores[-1] if z_scores else 0.0
                z_score_slope = (abs(z_scores[-1]) - abs(z_scores[-2])) if len(z_scores) >= 2 else 0.0
            except Exception as e:
                logger.error(f"Spread/Z-Score error for {leg_1}/{leg_2}: {e}")
                z_score = 0.0
                z_score_slope = 0.0

            strategy_data.append({
                "Strategy": f"{leg_1}/{leg_2}",
                "Leg 1": leg_1,
                "Leg 2": leg_2,
                "Correlation Coeff": correlation_coef if np.isfinite(correlation_coef) else 0.0,
                "Z-Score": z_score if np.isfinite(z_score) else 0.0,
                "Z-Score Slope": z_score_slope if np.isfinite(z_score_slope) else 0.0,
                "Hedge Ratio": beta if np.isfinite(beta) else 0.0
            })

            # Time series per pair
            time_series = []
            last_valid_values = {'zscore': 0.0, 'slope': 0.0, 'price': 0.0}
            for i in range(len(data)):
                if i < lookback_periods:
                    continue
                try:
                    window_data = data.iloc[i - lookback_periods:i + 1].astype(float)
                    window_spread = (window_data[leg_1] - beta * window_data[leg_2]).astype(float)

                    window_mean = float(window_spread.mean())
                    window_std = float(window_spread.std())

                    if not np.isfinite(window_std) or window_std == 0.0:
                        current_zscore = 0.0
                        prev_zscore = 0.0
                    else:
                        curr_val = float(window_spread.iloc[-1])
                        prev_val = float(window_spread.iloc[-2])
                        current_zscore = (curr_val - window_mean) / window_std
                        prev_zscore = (prev_val - window_mean) / window_std
                        current_zscore = 0.0 if not np.isfinite(current_zscore) else float(current_zscore)
                        prev_zscore = 0.0 if not np.isfinite(prev_zscore) else float(prev_zscore)

                    current_slope = current_zscore - prev_zscore
                    last_price = float(window_spread.iloc[-1]) if _finite(window_spread.iloc[-1]) else last_valid_values['price']

                    if _finite(current_zscore) and _finite(current_slope) and _finite(last_price):
                        time_series.append({
                            "date": data.index[i].strftime('%Y-%m-%d'),
                            "zscore": current_zscore,
                            "slope": current_slope,
                            "price": last_price
                        })
                        last_valid_values = {'zscore': current_zscore, 'slope': current_slope, 'price': last_price}
                    else:
                        time_series.append({
                            "date": data.index[i].strftime('%Y-%m-%d'),
                            "zscore": last_valid_values['zscore'],
                            "slope": last_valid_values['slope'],
                            "price": last_valid_values['price']
                        })
                except Exception as e:
                    logger.error(f"Time series error for {leg_1}/{leg_2} at i={i}: {e}")
                    time_series.append({
                        "date": data.index[i].strftime('%Y-%m-%d'),
                        "zscore": last_valid_values['zscore'],
                        "slope": last_valid_values['slope'],
                        "price": last_valid_values['price']
                    })
            time_series_data[f"{leg_1}/{leg_2}"] = time_series

        strategy_df = pd.DataFrame(strategy_data)
        strategy_df['time_series_data'] = [time_series_data] * len(strategy_df)
        return strategy_df

    def visualize_strategy_matrix(self, 
                               strategy_df: pd.DataFrame, 
                               matrix_types: List[str] = ['Correlation', 'Z-Score', 'Z-Score Slope', 'Hedge Ratio'],
                               group_1: Optional[List[str]] = None,
                               group_2: Optional[List[str]] = None,
                               figsize: Tuple[int, int] = None,
                               dpi: int = 300,
                               title: Optional[str] = 'Strategy Analysis Matrices',
                               color_scales: Dict[str, str] = None,
                               text_format: str = '.2f',
                               rotation: int = 45,
                               font_sizes: Dict[str, int] = None) -> Tuple[Optional[str], Optional[Dict]]:
        """
        Create enhanced visualization matrices for strategy analysis.
        Handles missing data and exceptions robustly.
        """
        if strategy_df.empty:
            logger.warning("No data to visualize.")
            return None, None
        try:
            if figsize is None:
                figsize = (10*len(matrix_types), 10)
            if color_scales is None:
                color_scales = {
                    'Correlation': 'RdYlGn', 
                    'Z-Score': 'RdYlBu', 
                    'Z-Score Slope': 'PiYG',
                    'Hedge Ratio': 'RdYlGn'
                }
            if font_sizes is None:
                font_sizes = {
                    'title': 28,
                    'suptitle': 22,
                    'tick_labels': 12,
                    'annotations': 10
                }

            def create_symmetric_matrix(df_in, value_column):
                try:
                    instruments = sorted(set(df_in['Leg 1'].tolist() + df_in['Leg 2'].tolist()))
                    matrix = pd.DataFrame(np.eye(len(instruments)), 
                                          index=instruments, 
                                          columns=instruments)
                    for _, row in df_in.iterrows():
                        leg_1, leg_2 = row['Leg 1'], row['Leg 2']
                        value = row.get(value_column, 0)
                        matrix.loc[leg_1, leg_2] = value
                        matrix.loc[leg_2, leg_1] = value
                    return matrix
                except Exception as e:
                    logger.error(f"Matrix creation error for {value_column}: {e}")
                    return pd.DataFrame()

            matrix_mapping = {
                'Correlation': 'Correlation Coeff',
                'Z-Score': 'Z-Score',
                'Z-Score Slope': 'Z-Score Slope',
                'Hedge Ratio': 'Hedge Ratio'
            }
            matrices = {
                matrix_type: create_symmetric_matrix(
                    strategy_df, matrix_mapping.get(matrix_type, matrix_type)
                ) for matrix_type in matrix_types if matrix_type in matrix_mapping
            }

            if group_1 and group_2:
                for key in matrices:
                    try:
                        matrices[key] = matrices[key].reindex(index=group_1, columns=group_2)
                    except Exception as e:
                        logger.error(f"Matrix reindex error for {key}: {e}")

            fig, axes = plt.subplots(1, len(matrix_types), figsize=figsize)
            if len(matrix_types) == 1:
                axes = [axes]

            vmin_vmax = {
                'Correlation': (-1, 1),
                'Z-Score': (-3, 3),
                'Z-Score Slope': (-0.5, 0.5),
                'Hedge Ratio': (-2, 2)
            }

            for i, matrix_type in enumerate(matrix_types):
                if matrix_type not in matrices or matrices[matrix_type].empty:
                    continue
                try:
                    vmin, vmax = vmin_vmax.get(matrix_type, (None, None))
                    sns.heatmap(
                        matrices[matrix_type], 
                        annot=True, 
                        cmap=color_scales[matrix_type], 
                        fmt=text_format, 
                        linewidths=0.5, 
                        ax=axes[i],
                        square=True,
                        vmin=vmin,
                        vmax=vmax,
                        annot_kws={"fontsize": font_sizes['annotations'], "fontweight": "bold"},
                        cbar_kws={'label': matrix_type}
                    )
                    axes[i].set_title(f"{matrix_type} Matrix", fontsize=font_sizes['suptitle'])
                    axes[i].set_xticklabels(
                        axes[i].get_xticklabels(), 
                        rotation=rotation, 
                        ha="right", 
                        fontsize=font_sizes['tick_labels']
                    )
                    axes[i].set_yticklabels(
                        axes[i].get_yticklabels(), 
                        fontsize=font_sizes['tick_labels']
                    )
                except Exception as e:
                    logger.error(f"Heatmap error for {matrix_type}: {e}")

            fig.suptitle(title, fontsize=font_sizes['title'])
            plt.tight_layout()
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', dpi=dpi, bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            plt.close(fig)

            matrix_data = {
                'matrices': {},
                'instruments': {
                    'rows': list(matrices[list(matrices.keys())[0]].index) if matrices and list(matrices.keys()) and not matrices[list(matrices.keys())[0]].empty else [],
                    'columns': list(matrices[list(matrices.keys())[0]].columns) if matrices and list(matrices.keys()) and not matrices[list(matrices.keys())[0]].empty else []
                },
                'time_series': strategy_df['time_series_data'].iloc[0] if not strategy_df.empty else {}
            }
            for matrix_type in matrices:
                try:
                    matrix_data['matrices'][matrix_type] = matrices[matrix_type].values.tolist() if not matrices[matrix_type].empty else []
                except Exception as e:
                    logger.error(f"Matrix tolist error for {matrix_type}: {e}")
                    matrix_data['matrices'][matrix_type] = []

            return image_base64, matrix_data
        except Exception as e:
            logger.error(f"Visualization error: {e}")
            return None, None
