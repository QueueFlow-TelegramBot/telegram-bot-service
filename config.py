import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
USER_SERVICE_URL = os.getenv("USER_SERVICE_URL", "http://user-service:8001")
SCHEDULING_SERVICE_URL = os.getenv("SCHEDULING_SERVICE_URL", "http://scheduling-service:8002")
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
RABBITMQ_EXCHANGE = os.getenv("RABBITMQ_EXCHANGE", "smartcampus")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
MOCK_SERVICES = os.getenv("MOCK_SERVICES", "false").lower() == "true"
