"""
Telegram bot integration for trading alerts and notifications
"""
import os
import asyncio
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass
from src.core.logger import logger

try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, ContextTypes
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("python-telegram-bot not installed. Install with: pip install python-telegram-bot")


@dataclass
class NotificationConfig:
    """Configuration for Telegram notifications"""
    enabled: bool
    token: str
    chat_ids: List[str]  # Multiple recipients
    include_charts: bool = False
    include_indicators: bool = True
    max_retries: int = 3
    retry_delay: int = 2  # seconds


class TelegramNotifier:
    """Handles Telegram notifications for trading events"""
    
    def __init__(self, config: NotificationConfig):
        """
        Initialize Telegram notifier
        
        Args:
            config: NotificationConfig with token and chat IDs
        """
        self.config = config
        self.bot = None
        self.is_connected = False
        
        if not TELEGRAM_AVAILABLE:
            logger.error("Telegram module not available")
            self.config.enabled = False
            return
        
        if config.enabled and config.token:
            try:
                self.bot = Bot(token=config.token)
                self.is_connected = True
                logger.info("Telegram notifier initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.config.enabled = False
    
    async def send_trade_signal(self, symbol: str, action: str, price: float,
                               confidence: float, indicators: Dict) -> bool:
        """
        Send trading signal notification
        
        Args:
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            price: Current price
            confidence: Signal confidence (0-100)
            indicators: Dict with RSI, MACD values
            
        Returns:
            True if sent successfully
        """
        if not self.config.enabled or not self.bot:
            return False
        
        # Format message
        emoji = "🟢" if action == "BUY" else "🔴" if action == "SELL" else "⚪"
        
        message = f"{emoji} *{action} Signal*\n\n"
        message += f"*Symbol:* {symbol}\n"
        message += f"*Price:* ${price:.2f}\n"
        message += f"*Confidence:* {confidence:.0f}%\n"
        
        if self.config.include_indicators and indicators:
            message += f"\n*Indicators:*\n"
            if indicators.get('rsi') is not None:
                message += f"  RSI: {indicators['rsi']:.1f}\n"
            if indicators.get('macd') is not None:
                message += f"  MACD: {indicators['macd']:.4f}\n"
                if indicators.get('signal') is not None:
                    message += f"  Signal: {indicators['signal']:.4f}\n"
        
        message += f"\n_Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return await self._send_message(message, parse_mode="Markdown")
    
    async def send_order_confirmation(self, symbol: str, action: str, quantity: float,
                                     price: float, order_id: str) -> bool:
        """
        Send order confirmation notification
        
        Args:
            symbol: Trading symbol
            action: 'BUY' or 'SELL'
            quantity: Order quantity
            price: Execution price
            order_id: Broker order ID
            
        Returns:
            True if sent successfully
        """
        if not self.config.enabled or not self.bot:
            return False
        
        emoji = "✅" if action == "BUY" else "❌" if action == "SELL" else "⏳"
        
        message = f"{emoji} *Order {action}*\n\n"
        message += f"*Symbol:* {symbol}\n"
        message += f"*Quantity:* {quantity}\n"
        message += f"*Price:* ${price:.2f}\n"
        message += f"*Total Value:* ${quantity * price:.2f}\n"
        message += f"*Order ID:* `{order_id}`\n"
        message += f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self._send_message(message, parse_mode="Markdown")
    
    async def send_daily_summary(self, stats: Dict) -> bool:
        """
        Send daily trading summary
        
        Args:
            stats: Dictionary with trading statistics
                - total_trades: int
                - winning_trades: int
                - losing_trades: int
                - total_pnl: float
                - win_rate: float
                - active_positions: int
                
        Returns:
            True if sent successfully
        """
        if not self.config.enabled or not self.bot:
            return False
        
        win_rate = stats.get('win_rate', 0)
        pnl = stats.get('total_pnl', 0)
        pnl_emoji = "📈" if pnl >= 0 else "📉"
        
        message = f"📊 *Daily Trading Summary*\n\n"
        message += f"*Total Trades:* {stats.get('total_trades', 0)}\n"
        message += f"*Winning:* {stats.get('winning_trades', 0)} "
        message += f"| *Losing:* {stats.get('losing_trades', 0)}\n"
        message += f"*Win Rate:* {win_rate:.1f}%\n"
        message += f"\n{pnl_emoji} *P&L:* ${pnl:.2f}\n"
        message += f"*Active Positions:* {stats.get('active_positions', 0)}\n"
        message += f"\n_Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_"
        
        return await self._send_message(message, parse_mode="Markdown")
    
    async def send_error_alert(self, title: str, error_message: str, symbol: Optional[str] = None) -> bool:
        """
        Send error/alert notification
        
        Args:
            title: Alert title
            error_message: Error details
            symbol: Optional trading symbol related to error
            
        Returns:
            True if sent successfully
        """
        if not self.config.enabled or not self.bot:
            return False
        
        message = f"⚠️ *{title}*\n\n"
        if symbol:
            message += f"*Symbol:* {symbol}\n"
        message += f"*Error:* `{error_message}`\n"
        message += f"*Time:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return await self._send_message(message, parse_mode="Markdown")
    
    async def _send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send message to all configured chat IDs
        
        Args:
            message: Message text
            parse_mode: Telegram parse mode
            
        Returns:
            True if sent successfully to at least one chat
        """
        if not self.config.enabled or not self.bot or not self.config.chat_ids:
            return False
        
        sent_count = 0
        for chat_id in self.config.chat_ids:
            try:
                await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
        
        return sent_count > 0
    
    def send_trade_signal_sync(self, symbol: str, action: str, price: float,
                              confidence: float, indicators: Dict) -> bool:
        """Synchronous wrapper for send_trade_signal"""
        if not TELEGRAM_AVAILABLE:
            return False
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Can't run async in running loop, queue it
                logger.warning("Event loop already running, skipping Telegram notification")
                return False
            return loop.run_until_complete(
                self.send_trade_signal(symbol, action, price, confidence, indicators)
            )
        except RuntimeError:
            # No event loop, create new one
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(
                    self.send_trade_signal(symbol, action, price, confidence, indicators)
                )
            finally:
                new_loop.close()
    
    def send_order_confirmation_sync(self, symbol: str, action: str, quantity: float,
                                    price: float, order_id: str) -> bool:
        """Synchronous wrapper for send_order_confirmation"""
        if not TELEGRAM_AVAILABLE:
            return False
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("Event loop already running, skipping Telegram notification")
                return False
            return loop.run_until_complete(
                self.send_order_confirmation(symbol, action, quantity, price, order_id)
            )
        except RuntimeError:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(
                    self.send_order_confirmation(symbol, action, quantity, price, order_id)
                )
            finally:
                new_loop.close()
    
    def send_daily_summary_sync(self, stats: Dict) -> bool:
        """Synchronous wrapper for send_daily_summary"""
        if not TELEGRAM_AVAILABLE:
            return False
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("Event loop already running, skipping Telegram notification")
                return False
            return loop.run_until_complete(self.send_daily_summary(stats))
        except RuntimeError:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self.send_daily_summary(stats))
            finally:
                new_loop.close()
    
    def send_error_alert_sync(self, title: str, error_message: str, symbol: Optional[str] = None) -> bool:
        """Synchronous wrapper for send_error_alert"""
        if not TELEGRAM_AVAILABLE:
            return False
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("Event loop already running, skipping Telegram notification")
                return False
            return loop.run_until_complete(self.send_error_alert(title, error_message, symbol))
        except RuntimeError:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(self.send_error_alert(title, error_message, symbol))
            finally:
                new_loop.close()
