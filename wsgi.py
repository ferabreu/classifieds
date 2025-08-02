import os

from app import create_app
from app.config import DevelopmentConfig, ProductionConfig, TestingConfig

config_map = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}
config_name = os.getenv("FLASK_ENV", "development").lower()
app = create_app(config_map.get(config_name, DevelopmentConfig))
