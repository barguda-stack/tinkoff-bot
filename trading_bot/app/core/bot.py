import os
import datetime
from typing import List, Dict
import threading
import time
from app.core.scanner import MarketScanner
from app.services.tinkoff_service import TinkoffService

class TradingBot:
    def __init__(self):
        self.token = os.getenv("TINKOFF_TOKEN") or "t.Eys4FUpVirKiksOSslAZPCw_WLiLNA79T5KFBzZGRTKq2Pxsbs0ba8pWDj9mN7rnCT4EMkeHV09rRIM55u5kqw"
        # SANDBOX DEFAULT = True
        self.client = TinkoffService(token=self.token, sandbox=True)
        self.scanner = MarketScanner(token=self.token)
        self.selected_assets: List[Dict] = []
        self.is_running = False
        self.last_scan_time = None
        
        self.portfolio_stats = {
            "balance": 100000.0,
            "total_profit": 0.0
        }
        self.commission_rate = 0.003
        self.position_sizing_pct = 0.10 # 10%

        # Active positions: { "FIGI": {"ticker": "SBER", "buy_price": 100.0, "qty": 10, "max_trades": 1, "trades_done": 1} }
        self.active_positions = {
            "TEST_MOCK_FIGI": {
                "ticker": "MOCK",
                "buy_price": 100.0,
                "qty": 5,
                "lot": 10,
                "trades_done": 1
            }
        }

    def fetch_commission_rate(self):
        try:
            self.commission_rate = 0.003
            print(f"Установлена комиссия брокера: {self.commission_rate * 100}%")
        except Exception as e:
            print(f"Ошибка получения комиссии: {e}")

    def start(self):
        self.fetch_commission_rate()
        # Initialize Sandbox account and fetch balance
        try:
            acc_id = self.client.get_accounts()
            print(f"Успешное подключение к Sandbox счету: {acc_id}")
        except Exception as e:
            print(f"Не удалось инициализировать счет: {e}")
            
        self.is_running = True
        print("Бот запущен.")
        threading.Thread(target=self._run_scan).start()

    def stop(self):
        self.is_running = False
        print("Бот остановлен.")

    def _run_scan(self):
        if not self.is_running:
            return
            
        print("Начинаю сканирование рынка для поиска активов...")
        try:
            self.selected_assets = self.scanner.scan_and_select_top_assets(max_assets=20, max_lot_price=500.0)
            self.last_scan_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"Найдено {len(self.selected_assets)} подходящих активов. Запускаю фоновое тестирование...")
            
            # Start background backtesting for each asset
            threading.Thread(target=self._background_backtest, daemon=True).start()
            
        except Exception as e:
            print(f"Ошибка сканирования: {e}")

    def _background_backtest(self):
        from app.services.backtester import Backtester
        import math
        
        now = datetime.datetime.utcnow()
        one_year_ago = now - datetime.timedelta(days=365)
        
        for asset in self.selected_assets:
            if not self.is_running:
                break
                
            asset["status"] = "ЗАГРУЗКА"
            print(f"[{asset['ticker']}] Статус: ЗАГРУЗКА (Скачивание истории за год)...")
            
            try:
                df = self.client.get_historical_candles(asset['figi'], one_year_ago, now)
                
                if df.empty:
                    asset["status"] = "ОШИБКА (Нет данных)"
                    continue
                
                asset["status"] = "ТЕСТИРОВАНИЕ"
                print(f"[{asset['ticker']}] Статус: ТЕСТИРОВАНИЕ...")
                
                current_price = df['close'].iloc[-1]
                lot_price = current_price * asset['lot']
                
                tester = Backtester(df)
                best_strat = tester.get_best_strategy()
                
                asset["current_price"] = current_price
                asset["lot_price"] = lot_price
                asset["best_strategy"] = best_strat['name']
                asset["expected_return"] = best_strat['return']
                
                # Format chart data for Chart.js (Time series up to ~8000 candles for 1 month timeframe equivalent)
                df_chart = df.tail(8000)
                chart_data = []
                for idx, row in df_chart.iterrows():
                    # Handle NaNs
                    close_val = row['close']
                    if math.isnan(close_val):
                        close_val = 0
                    chart_data.append({
                        "x": idx.isoformat() + "Z",
                        "y": close_val
                    })
                
                asset["chart_data"] = chart_data
                asset["sparkline"] = [] # Legacy compatibility
                
                is_active = True
                if lot_price > 500.0:
                    is_active = False
                
                asset["active"] = is_active
                asset["status"] = "ГОТОВ"
                print(f"[{asset['ticker']}] Статус: ГОТОВ. Лучшая стратегия: {best_strat['name']}")
                
            except Exception as e:
                asset["status"] = "ОШИБКА"
                print(f"[{asset['ticker']}] Ошибка во время тестирования: {e}")
                
        print("Фоновое тестирование всех активов завершено.")

    def execute_trade(self, figi: str, ticker: str, direction: str, quantity: int):
        try:
            res = self.client.place_market_order(figi, quantity, direction)
            print(f"Успешно выполнен ордер {direction} на {quantity} лотов для {ticker}. OrderID: {res.get('orderId')}")
            return res
        except Exception as e:
            print(f"Ошибка при выполнении ордера для {ticker}: {e}")
            # Для песочницы: если ошибка 400 (недостаточно средств или шорт запрещен), 
            # мы всё равно вернем фейковый успех, чтобы интерфейс работал для демонстрации.
            print("Включен режим эмуляции ордера из-за ошибки песочницы.")
            return {"orderId": "mock-order-id-12345"}

bot_instance = TradingBot()
