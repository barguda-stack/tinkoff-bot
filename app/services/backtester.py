import pandas as pd
import numpy as np
from typing import Dict, Any

class Backtester:
    def __init__(self, data: pd.DataFrame):
        self.data = data

    def run_sma_crossover(self, short_window: int = 10, long_window: int = 50) -> float:
        """Simple Moving Average Crossover Strategy."""
        if len(self.data) < long_window:
            return 0.0

        df = self.data.copy()
        df['sma_short'] = df['close'].rolling(window=short_window).mean()
        df['sma_long'] = df['close'].rolling(window=long_window).mean()
        
        # 1 if short > long, else 0
        df['signal'] = np.where(df['sma_short'] > df['sma_long'], 1, 0)
        df['position'] = df['signal'].diff()
        
        # Calculate returns
        df['daily_return'] = df['close'].pct_change()
        # Strategy return (assuming we hold when signal is 1)
        # Shift signal by 1 to represent return for next day based on today's signal
        df['strategy_return'] = df['daily_return'] * df['signal'].shift(1)
        
        cumulative_return = (1 + df['strategy_return'].fillna(0)).prod() - 1
        return cumulative_return

    def run_rsi_strategy(self, window: int = 14, overbought: int = 70, oversold: int = 30) -> float:
        """RSI Strategy (Buy when oversold, sell when overbought)."""
        if len(self.data) < window + 1:
            return 0.0
            
        df = self.data.copy()
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # Simplified logic: 1 when holding, 0 otherwise
        # Buy on < 30, Hold until > 70
        signals = []
        holding = False
        for rsi_val in df['rsi']:
            if pd.isna(rsi_val):
                signals.append(0)
            elif rsi_val < oversold:
                holding = True
                signals.append(1)
            elif rsi_val > overbought:
                holding = False
                signals.append(0)
            else:
                signals.append(1 if holding else 0)
                
        df['signal'] = signals
        df['daily_return'] = df['close'].pct_change()
        df['strategy_return'] = df['daily_return'] * df['signal'].shift(1)
        
        cumulative_return = (1 + df['strategy_return'].fillna(0)).prod() - 1
        return cumulative_return

    def get_best_strategy(self) -> Dict[str, Any]:
        """Runs all strategies and returns the best one."""
        sma_return = self.run_sma_crossover()
        rsi_return = self.run_rsi_strategy()
        
        strategies = {
            "SMA_Crossover": sma_return,
            "RSI": rsi_return
        }
        
        best_name = max(strategies, key=strategies.get)
        best_return = strategies[best_name]
        
        return {
            "name": best_name,
            "return": best_return,
            "all_results": strategies
        }
