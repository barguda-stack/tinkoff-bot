from apscheduler.schedulers.background import BackgroundScheduler
from app.core.bot import bot_instance
from app.services.backtester import Backtester
import datetime
import math

def run_trading_cycle():
    """Main trading loop that evaluates active assets and manages positions."""
    if not bot_instance.is_running:
        return
        
    print("Executing trading cycle...")
    
    # 1. Evaluate open positions (Sell logic)
    for figi, pos in list(bot_instance.active_positions.items()):
        ticker = pos['ticker']
        buy_price = pos['buy_price']
        qty = pos['qty']
        
        # Get latest data
        now = datetime.datetime.utcnow()
        one_day_ago = now - datetime.timedelta(days=1)
        try:
            df = bot_instance.client.get_historical_candles(figi, one_day_ago, now)
            if df.empty: continue
            current_price = df['close'].iloc[-1]
            
            # Commission calculation
            # Break-even = BuyPrice * (1 + commission_buy) / (1 - commission_sell)
            breakeven_price = buy_price * (1 + bot_instance.commission_rate) / (1 - bot_instance.commission_rate)
            
            # We exit if consensus > 60% says SELL
            # We can run our multifactor test on the data to see if signal is 0 (Sell/Hold)
            tester = Backtester(df)
            signals = tester.compute_all_indicators()
            
            # Simple sell condition: if current price < breakeven and we are falling fast (stop loss)
            # OR if we made good profit and indicators say sell.
            # (Just a mock logic placeholder for the complex consensus)
            
            should_sell = False
            
            if should_sell:
                res = bot_instance.execute_trade(figi, ticker, "SELL", qty)
                if res:
                    profit = (current_price - buy_price) * qty * pos.get('lot', 1)
                    bot_instance.portfolio_stats['total_profit'] += profit
                    del bot_instance.active_positions[figi]
                    
        except Exception as e:
            print(f"Error evaluating position {ticker}: {e}")
            
    # 2. Evaluate active assets to open new positions (Buy logic)
    for asset in bot_instance.selected_assets:
        if not asset.get('active'):
            continue
            
        figi = asset['figi']
        ticker = asset['ticker']
        
        # Check max trades limit
        if figi in bot_instance.active_positions:
            pos = bot_instance.active_positions[figi]
            if pos['trades_done'] >= asset.get('max_trades', 1):
                continue
                
        now = datetime.datetime.utcnow()
        one_day_ago = now - datetime.timedelta(days=1)
        try:
            df = bot_instance.client.get_historical_candles(figi, one_day_ago, now)
            if df.empty: continue
            
            current_price = df['close'].iloc[-1]
            tester = Backtester(df)
            # Check if consensus says buy right now
            # To simplify, we check if the last candle signal would be 1
            consensus = tester.run_consensus_strategy() # Returns float, but we want the last signal actually
            
            # Assuming consensus logic says BUY (Mock condition: True for demo)
            should_buy = True 
            
            if should_buy:
                # Position Sizing
                balance = bot_instance.portfolio_stats['balance']
                max_money = balance * bot_instance.position_sizing_pct
                
                # Calculate lots to buy
                lot_price = current_price * asset['lot']
                lots_to_buy = math.floor(max_money / lot_price)
                
                # Respect user setting max_lots
                max_allowed_lots = asset.get('max_lots', 1)
                lots_to_buy = min(lots_to_buy, max_allowed_lots)
                
                if lots_to_buy > 0:
                    res = bot_instance.execute_trade(figi, ticker, "BUY", lots_to_buy)
                    if res:
                        bot_instance.active_positions[figi] = {
                            "ticker": ticker,
                            "buy_price": current_price,
                            "qty": lots_to_buy,
                            "lot": asset['lot'],
                            "trades_done": 1 # increment if buying multiple times
                        }
                        
        except Exception as e:
            print(f"Error evaluating buy for {ticker}: {e}")

def start_scheduler():
    scheduler = BackgroundScheduler()
    # Market scan (premarket) every 60 minutes
    scheduler.add_job(bot_instance._run_scan, 'interval', minutes=60)
    
    # Trading cycle every 5 minutes (matching timeframe)
    scheduler.add_job(run_trading_cycle, 'interval', minutes=5)
    
    scheduler.start()
    print("Планировщик задач запущен (Премаркет каждый час, Торговля каждые 5 мин).")
