import pandas as pd
import numpy as np
from typing import Dict, Any
import ta

class Backtester:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def compute_all_indicators(self):
        df = self.data.copy()
        # Since we use 1 day of 5 min candles, we have ~ 100-200 candles.
        # Ensure we don't crash if len < 50
        if len(df) < 50:
            # fill with nan to avoid errors
            for c in ['sma_20','sma_50','macd','macd_signal','rsi','stoch_k','stoch_d','bb_low','close']:
                if c not in df: df[c] = np.nan
            return df

        # Trend Indicators
        df['sma_20'] = ta.trend.sma_indicator(df['close'], window=20)
        df['sma_50'] = ta.trend.sma_indicator(df['close'], window=50)
        df['ema_12'] = ta.trend.ema_indicator(df['close'], window=12)
        df['ema_26'] = ta.trend.ema_indicator(df['close'], window=26)
        macd = ta.trend.MACD(df['close'])
        df['macd'] = macd.macd()
        df['macd_signal'] = macd.macd_signal()
        df['adx'] = ta.trend.ADXIndicator(df['high'], df['low'], df['close']).adx()
        df['cci'] = ta.trend.CCIIndicator(df['high'], df['low'], df['close']).cci()

        # Momentum Indicators
        df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
        stoch = ta.momentum.StochasticOscillator(df['high'], df['low'], df['close'])
        df['stoch_k'] = stoch.stoch()
        df['stoch_d'] = stoch.stoch_signal()
        df['williams_r'] = ta.momentum.WilliamsRIndicator(df['high'], df['low'], df['close']).williams_r()

        # Volatility Indicators
        bb = ta.volatility.BollingerBands(df['close'])
        df['bb_high'] = bb.bollinger_hband()
        df['bb_low'] = bb.bollinger_lband()
        df['atr'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close']).average_true_range()

        return df

    def run_consensus_strategy(self) -> float:
        df = self.compute_all_indicators()
        if len(df) < 50:
            return 0.0

        signals = []
        for i in range(len(df)):
            row = df.iloc[i]
            buy_votes = 0
            total_votes = 5 

            # 1. Moving Averages Crossover
            if pd.notna(row.get('sma_20')) and pd.notna(row.get('sma_50')) and row['sma_20'] > row['sma_50']:
                buy_votes += 1
                
            # 2. MACD
            if pd.notna(row.get('macd')) and pd.notna(row.get('macd_signal')) and row['macd'] > row['macd_signal']:
                buy_votes += 1
                
            # 3. RSI Oversold recovery
            if pd.notna(row.get('rsi')) and 30 < row['rsi'] < 50:
                buy_votes += 1
                
            # 4. Stochastic
            if pd.notna(row.get('stoch_k')) and pd.notna(row.get('stoch_d')) and row['stoch_k'] > row['stoch_d']:
                buy_votes += 1
                
            # 5. Bollinger Bands bounce
            if pd.notna(row.get('bb_low')) and pd.notna(row.get('close')) and row['close'] > row['bb_low']:
                buy_votes += 1

            if (buy_votes / total_votes) > 0.6:
                signals.append(1)
            else:
                signals.append(0)

        df['signal'] = signals
        df['daily_return'] = df['close'].pct_change()
        df['strategy_return'] = df['daily_return'] * df['signal'].shift(1)
        
        cumulative_return = (1 + df['strategy_return'].fillna(0)).prod() - 1
        return cumulative_return

    def get_best_strategy(self) -> Dict[str, Any]:
        consensus_return = self.run_consensus_strategy()
        return {
            "name": "Consensus_60Pct",
            "return": consensus_return,
            "all_results": {"Consensus_60Pct": consensus_return}
        }
