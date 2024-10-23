import os
import logging
import asyncio
import aiohttp
import datetime

from telebot import async_telebot
from fastapi.security import APIKeyHeader
from fastapi import FastAPI, HTTPException, Depends


class Application:
    def __init__(self):
        self.logger = self.setup_logging()
        self.app = FastAPI()
        self.load_config()
        self.setup_routes()
        self.session = None

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.INFO)
        return logger

    def load_config(self):
        self.remote_url = os.getenv('REMOTE_URL')
        self.check_interval = float(os.getenv('CHECK_INTERVAL', '60'))
        self.retry_interval = int(os.getenv('RETRY_INTERVAL', '900'))
        self.ssl_token = os.getenv('SSL_TOKEN')
        self.telegram_token = os.getenv('TELEGRAM_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        self.logger.info("Configuration loaded successfully")

    def setup_routes(self):
        token_header = APIKeyHeader(name="X-Token")

        async def verify_token(ssl_token: str = Depends(token_header)):
            if ssl_token != self.ssl_token:
                raise HTTPException(status_code=403, detail="Invalid Token")
            return ssl_token
        
        @self.app.get('/health')
        async def health_check(ssl_token: str = Depends(verify_token)):
            return {"status": "OK"}
        
        @self.app.on_event("startup")
        async def startup_event():
            self.session = aiohttp.ClientSession()
            self.bot = async_telebot.AsyncTeleBot(token=self.telegram_token)
            asyncio.create_task(self.main())

        @self.app.on_event("shutdown")
        async def shutdown_event():
            await self.session.close()
            await self.bot.session.close()

    async def check_health(self):
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            async with self.session.get(
                f"{self.remote_url}/health",
                timeout=60,
                headers={"X-Token": self.ssl_token},
                ssl=True
            ) as response:
                response.raise_for_status()
                self.logger.info(
                    f"[{current_time}] Health check successful for {self.remote_url[:-5]}"
                )
                return True, None
        except Exception as e:
            self.logger.error(f"[{current_time}] Health check failed for {self.remote_url[:-5]}: {e}")
            return False, e

    async def send_telegram_message(self, message: str):
        try:
            await self.bot.send_message(
            chat_id=self.telegram_chat_id,
            text=message
            )
            self.logger.info(f"Telegram message sent: {message}")
        except Exception as e:
            self.logger.error(f"Failed to send Telegram message: {e}")

    async def main(self):
        self.logger.info("Starting health check script")

        while True:
            is_healthy, error_message = await self.check_health()
            if not is_healthy:
                message = f"{self.remote_url[:-5]} is not responding.\nError: {error_message}"
                await self.send_telegram_message(message)
                self.logger.warning(
                f"Waiting for {self.retry_interval} seconds before next check"
                )
                await asyncio.sleep(self.retry_interval)

            else:
                self.logger.info(
                    f"Waiting for {self.check_interval:.1f} seconds before next check"
                )
                await asyncio.sleep(self.check_interval)


application = Application()
app = application.app