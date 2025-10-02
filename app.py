#!/usr/bin/env python3
"""
Mock Flask API for Trading Bot - Uses Simulated Data
For testing the React dashboard when market is closed
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import threading
import time
from datetime import datetime
import random
import os

app = Flask(__name__)
CORS(app)

class MockTradingBot:
    """Mock trading bot with simulated data"""
    
    def __init__(self):
        self.bot_thread = None
        self.is_running = False
        self.initial_value = 10000
        self.cash = 10000
        self.shares_held = 0
        self.current_price = 175.0
        self.bot_state = {
            'status': 'stopped',
            'current_position': None,
            'portfolio_value': 10000,
            'cash': 10000,
            'total_pl': 0,
            'total_pl_pct': 0,
            'last_update': None,
            'last_action': 'HOLD',
            'market_open': True  # Simulate market always open for testing
        }
        self.trade_history = []
        self.performance_history = []
        self.config = {}
        
    def initialize(self, config):
        """Initialize bot with config"""
        self.config = config
        self.bot_state['status'] = 'initialized'
        print(f"Mock bot initialized with ticker: {config.get('ticker', 'AAPL')}")
        return {'success': True, 'message': 'Mock bot initialized'}
    
    def simulate_price_movement(self):
        """Simulate realistic price movements"""
        # Random walk with slight upward bias
        change_percent = random.gauss(0.001, 0.015)  # 0.1% mean, 1.5% std dev
        self.current_price *= (1 + change_percent)
        return self.current_price
    
    def make_trading_decision(self):
        """Simulate trading decisions"""
        # Simple strategy: buy if price drops, sell if it rises significantly
        actions = ['HOLD', 'BUY', 'SELL']
        
        if self.shares_held == 0:
            # 20% chance to buy
            return 1 if random.random() < 0.2 else 0
        else:
            # 15% chance to sell if we have shares
            return 2 if random.random() < 0.15 else 0
    
    def execute_mock_trade(self, action):
        """Execute simulated trade"""
        timestamp = datetime.now().isoformat()
        
        if action == 1 and self.shares_held == 0:  # BUY
            shares_to_buy = int(self.cash * 0.95 / self.current_price)
            if shares_to_buy > 0:
                cost = shares_to_buy * self.current_price
                self.cash -= cost
                self.shares_held = shares_to_buy
                
                trade = {
                    'timestamp': timestamp,
                    'action': 'BUY',
                    'shares': shares_to_buy,
                    'price': self.current_price,
                    'order_id': f'mock-{random.randint(1000, 9999)}'
                }
                self.trade_history.append(trade)
                self.bot_state['last_action'] = 'BUY'
                print(f"Mock BUY: {shares_to_buy} shares @ ${self.current_price:.2f}")
                
        elif action == 2 and self.shares_held > 0:  # SELL
            revenue = self.shares_held * self.current_price
            profit = revenue - (self.shares_held * (self.bot_state['portfolio_value'] - self.cash) / max(self.shares_held, 1))
            self.cash += revenue
            
            trade = {
                'timestamp': timestamp,
                'action': 'SELL',
                'shares': self.shares_held,
                'price': self.current_price,
                'order_id': f'mock-{random.randint(1000, 9999)}',
                'profit': profit
            }
            self.trade_history.append(trade)
            self.bot_state['last_action'] = 'SELL'
            print(f"Mock SELL: {self.shares_held} shares @ ${self.current_price:.2f}")
            self.shares_held = 0
        else:
            self.bot_state['last_action'] = 'HOLD'
    
    def update_state(self):
        """Update bot state"""
        position_value = self.shares_held * self.current_price
        portfolio_value = self.cash + position_value
        total_pl = portfolio_value - self.initial_value
        total_pl_pct = (total_pl / self.initial_value) * 100
        
        self.bot_state.update({
            'portfolio_value': portfolio_value,
            'cash': self.cash,
            'current_position': {
                'qty': self.shares_held,
                'avg_entry_price': self.current_price,
                'current_price': self.current_price,
                'market_value': position_value,
                'unrealized_pl': position_value - (self.shares_held * self.current_price) if self.shares_held > 0 else 0
            } if self.shares_held > 0 else None,
            'total_pl': total_pl,
            'total_pl_pct': total_pl_pct,
            'last_update': datetime.now().isoformat(),
            'market_open': True
        })
        
        # Store performance history
        self.performance_history.append({
            'timestamp': datetime.now().isoformat(),
            'portfolio_value': portfolio_value,
            'cash': self.cash,
            'position_value': position_value
        })
        
        # Keep only last 1000 records
        if len(self.performance_history) > 1000:
            self.performance_history = self.performance_history[-1000:]
    
    def trading_loop(self):
        """Main trading loop"""
        print("Mock trading bot started")
        check_interval = self.config.get('check_interval', 5)  # Default 5 seconds for testing
        
        while self.is_running:
            try:
                self.bot_state['status'] = 'active'
                
                # Simulate price movement
                self.simulate_price_movement()
                
                # Make trading decision
                action = self.make_trading_decision()
                
                # Execute trade
                self.execute_mock_trade(action)
                
                # Update state
                self.update_state()
                
                # Wait
                time.sleep(check_interval)
                
            except Exception as e:
                print(f"Error in mock trading loop: {e}")
                time.sleep(check_interval)
        
        self.bot_state['status'] = 'stopped'
        print("Mock trading bot stopped")
    
    def start(self):
        """Start the bot"""
        if self.is_running:
            return {'success': False, 'error': 'Bot already running'}
        
        if not self.config:
            return {'success': False, 'error': 'Bot not initialized'}
        
        self.is_running = True
        self.bot_thread = threading.Thread(target=self.trading_loop, daemon=True)
        self.bot_thread.start()
        
        return {'success': True, 'message': 'Mock bot started'}
    
    def stop(self):
        """Stop the bot"""
        if not self.is_running:
            return {'success': False, 'error': 'Bot not running'}
        
        self.is_running = False
        if self.bot_thread:
            self.bot_thread.join(timeout=5)
        
        self.bot_state['status'] = 'stopped'
        return {'success': True, 'message': 'Mock bot stopped'}
    
    def get_state(self):
        """Get current state"""
        return self.bot_state
    
    def get_trades(self, limit=50):
        """Get recent trades"""
        return self.trade_history[-limit:]
    
    def get_performance(self, limit=200):
        """Get performance history"""
        return self.performance_history[-limit:]


# Create bot instance
bot = MockTradingBot()


# API Endpoints
@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})


@app.route('/api/bot/initialize', methods=['POST'])
def initialize_bot():
    """Initialize bot"""
    config = request.json
    result = bot.initialize(config)
    return jsonify(result)


@app.route('/api/bot/start', methods=['POST'])
def start_bot():
    """Start bot"""
    result = bot.start()
    return jsonify(result)


@app.route('/api/bot/stop', methods=['POST'])
def stop_bot():
    """Stop bot"""
    result = bot.stop()
    return jsonify(result)


@app.route('/api/bot/status', methods=['GET'])
def get_status():
    """Get status"""
    state = bot.get_state()
    state['next_market_open'] = datetime.now().isoformat()
    return jsonify(state)


@app.route('/api/bot/trades', methods=['GET'])
def get_trades():
    """Get trades"""
    limit = request.args.get('limit', 50, type=int)
    trades = bot.get_trades(limit)
    return jsonify({'trades': trades, 'count': len(trades)})


@app.route('/api/bot/performance', methods=['GET'])
def get_performance():
    """Get performance"""
    limit = request.args.get('limit', 200, type=int)
    performance = bot.get_performance(limit)
    return jsonify({'performance': performance, 'count': len(performance)})


@app.route('/api/market/status', methods=['GET'])
def market_status():
    """Market status"""
    return jsonify({
        'is_open': True,
        'next_open': datetime.now().isoformat(),
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    print("="*60)
    print("MOCK TRADING API SERVER")
    print("="*60)
    print(f"Running on http://localhost:{port}")
    print("This is a MOCK server with simulated data")
    print("No real trading or API connections")
    print("="*60)
    app.run(host='0.0.0.0', port=port, debug=False)