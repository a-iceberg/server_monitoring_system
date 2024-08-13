import requests
import time
import os
import logging
from telebot import TeleBot


class Application:
    def __init__(self):
        self.logger = self.setup_logging()
        self.load_config()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger

    def load_config(self):
        self.remote_url = os.getenv('REMOTE_URL')
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '1'))
        self.retry_interval = int(os.getenv('RETRY_INTERVAL', '900'))
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        self.logger.info("Configuration loaded successfully")

    def check_health(self):
        try:
            response = requests.get(self.remote_url, timeout=None, verify=True)
            response.raise_for_status()
            self.logger.info(f"Health check successful for {self.remote_url}")
            return True
        except requests.RequestException as e:
            self.logger.error(f"Health check failed for {self.remote_url}: {str(e)}")
            return False

    def send_telegram_message(self, message: str):
        try:
            self.bot.send_message(chat_id=self.telegram_chat_id, text=message)
            self.logger.info(f"Telegram message sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {str(e)}")

    def main(self):
        self.logger.info("Starting health check script")
        self.bot = TeleBot(token=self.telegram_token)

        while True:
            if not self.check_health():
                message = f"Error: {self.remote_url} is not responding"
                self.send_telegram_message(message)
                self.logger.warning(f"Waiting for {self.retry_interval} seconds before next check")
                time.sleep(self.retry_interval)
            else:
                self.logger.debug(f"Waiting for {self.check_interval} seconds before next check")
                time.sleep(self.check_interval)

application = Application()
if __name__ == '__main__':
    application.main()