from app import create_app
from config import DevelopmentConfig, TestingConfig, ProductionConfig
import os

config_map = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
config_name = os.getenv('FLASK_ENV', 'development').lower()
app = create_app(config_map.get(config_name, DevelopmentConfig))