# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

WSGI entry point for the Flask application.

Maps environment-based configuration and creates the Flask app instance for deployment.
"""

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
