import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import statsmodels.api as sm
import base64
import io
import logging
from itertools import combinations
from typing import List, Optional, Dict, Tuple
from pandas_datareader import data as web
import urllib3
import matplotlib

# ======================================
# CONFIGURATION
# ======================================
matplotlib.use('Agg')  # for headless plotting
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ======================================
# CLASS DEFINITION
# ======================================
class MarketDataAnalyzer:
    """
    Fetch, preprocess, analyze, and visualize market data from Stooq.
    """

    def __init__(self, instruments_config: Dict[str, Dict[str, str]]):
        self.instruments_config = instruments_config

    # -------------------------------------------------------------
    def fetch_market_data(self, instruments: List[str], interval="1D", count=300) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC data from Stooq for given instruments.
        Returns a DataFrame with columns: ['time', 'product', 'close']
        """
        interval_map = {"1H": "hour", "1D": "daily"}
        interval = interval_map.get(interval, interval)

        all_data = []
        for symbol in instruments:
            try:
                df = web.DataReader(symbol, 'stooq')
                if df is None or df.empty:
                    logger.warning(f"No data for {symbol}")
                    continue

                df = df.sort_index()  # ascending by time
                df = df.tail(count).copy()
                df['product'] = symbol
                df['time'] = df.index
                df.rename(columns={'Close': 'close'}, inplace=True)
                all_data.append(df[['time', 'product', 'close']])

                logger.info(f"Fetched {len(df)} records for {symbol}")

            except Exception as e:
                logger.error(f"Error fetching data for {symbol}: {e}")

        return pd.concat(all_data, ignore_index=True) if all_data else None

    # -------------------------------------------------------------
    def preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Convert to wide format: index=time, columns=products, values=close
        """
        if df is None or df.empty:
            logger.error("No data to preprocess")
            return pd.DataFrame()

        try:
            df['time'] = pd.to_datetime(df['time'], errors='coerce')
            df = df.dropna(subset=['time'])
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df = df.drop_duplicates(subset=['time', 'product'], keep='last')

            pivot_df = df.pivot(index='time', columns='product', values='close').sort_index()
            pivot_df = pivot_df.dropna(how='all', axis=1)
            logger.info(f"Preprocessed data shape: {pivot_df.shape}")
            return pivot_df

        except Exception as e:
            logger.error(f"Preprocessing error: {e}")
            return pd.DataFrame()

    # -------------------------------------------------------------
    def compute_hedge_ratios(
        self,
        df: pd.DataFrame,
        instruments_1: List[str],
        instruments_2: Optional[List[str]] = None,
        cross_compare=True,
        lookback_periods=5
    ) -> pd.DataFrame:
        """
        Compute hedge ratios, correlations, Z-scores, and slopes.
        """
        if df is None or df.empty:
            logger.error("No data for hedge computation")
            return pd.DataFrame()

        df = df.apply(pd.to_numeric, errors='coerce').dropna(axis=1, how='all')

        if instruments_2 is None:
            instruments_2 = instruments_1

        if cross_compare:
            pairs = [(a, b) for a in instruments_1 for b in instruments_2 if a != b]
        else:
            pairs = list(combinations(instruments_1, 2))

        results = []

        for leg1, leg2 in pairs:
            if leg1 not in df.columns or leg2 not in df.columns:
                continue

            sub = df[[leg1, leg2]].dropna()
            if len(sub) < 10:
                continue

            try:
                corr = sub[leg1].corr(sub[leg2])

                # OLS regression to get hedge ratio
                X = sm.add_constant(sub[leg2])
                model = sm.OLS(sub[leg1], X).fit()
                beta = model.params[1]

                spread = sub[leg1] - beta * sub[leg2]
                z = (spread - spread.mean()) / spread.std()
                z_slope = (abs(z.iloc[-1]) - abs(z.iloc[-2])) if len(z) >= 2 else 0.0

                results.append({
                    "Strategy": f"{leg1}/{leg2}",
                    "Leg 1": leg1,
                    "Leg 2": leg2,
                    "Correlation Coeff": corr,
                    "Hedge Ratio": beta,
                    "Z-Score": z.iloc[-1],
                    "Z-Score Slope": z_slope
                })

            except Exception as e:
                logger.error(f"Error computing {leg1}/{leg2}: {e}")

        return pd.DataFrame(results)

    # -------------------------------------------------------------
    def visualize_strategy_matrix(
        self,
        strategy_df: pd.DataFrame,
        matrix_types: List[str] = ['Correlation', 'Z-Score', 'Z-Score Slope', 'Hedge Ratio'],
        figsize: Tuple[int, int] = (20, 6),
        dpi=300,
        title='Strategy Analysis Matrices'
    ) -> Optional[str]:
        """
        Generate heatmaps for strategy matrices.
        """
        if strategy_df.empty:
            logger.error("No data to visualize")
            return None

        mapping = {
            'Correlation': 'Correlation Coeff',
            'Z-Score': 'Z-Score',
            'Z-Score Slope': 'Z-Score Slope',
            'Hedge Ratio': 'Hedge Ratio'
        }

        fig, axes = plt.subplots(1, len(matrix_types), figsize=figsize)
        if len(matrix_types) == 1:
            axes = [axes]

        for i, m_type in enumerate(matrix_types):
            col = mapping[m_type]
            instruments = sorted(set(strategy_df['Leg 1']).union(strategy_df['Leg 2']))
            mat = pd.DataFrame(np.nan, index=instruments, columns=instruments)

            for _, r in strategy_df.iterrows():
                mat.loc[r['Leg 1'], r['Leg 2']] = r[col]
                mat.loc[r['Leg 2'], r['Leg 1']] = r[col]

            sns.heatmap(
                mat,
                annot=True,
                fmt=".2f",
                cmap="RdYlGn",
                square=True,
                ax=axes[i],
                cbar_kws={'label': m_type}
            )
            axes[i].set_title(m_type, fontsize=14)
            axes[i].tick_params(axis='x', rotation=45)

        fig.suptitle(title, fontsize=18)
        plt.tight_layout()

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=dpi, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        return img_base64


# ======================================
# SAMPLE EXECUTION
# ======================================
if __name__ == "__main__":
    instruments = ["SPY.US", "AAPL.US", "MSFT.US", "META.US"]  # Example US stocks from Stooq

    analyzer = MarketDataAnalyzer(instruments_config={})
    df_raw = analyzer.fetch_market_data(instruments)
    df_pre = analyzer.preprocess_data(df_raw)

    strat_df = analyzer.compute_hedge_ratios(df_pre, instruments)
    print(strat_df.head())

    image = analyzer.visualize_strategy_matrix(strat_df)
    if image:
        print("Visualization generated (base64 length):", len(image))
