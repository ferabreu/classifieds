# SPDX-License-Identifier: GPL-2.0-only
# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the GNU General Public License v2.0 (GPL-2.0-only).
# See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

Test script for reserved category name validation.

Validates that reserved URL names (admin, static, etc.) are properly rejected in category creation.
"""

from app import create_app
from app.config import TestingConfig
from app.models import Category, User, db


def run_tests():
    app = create_app(TestingConfig)
    results = {}
    with app.app_context():
        db.create_all()
        # Seed admin user
        admin = User(
            email="admin@classifieds.io",
            first_name="Admin",
            last_name="User",
            is_admin=True,
        )
        admin.set_password("admin")
        db.session.add(admin)
        db.session.commit()

        client = app.test_client()
        # Login as admin
        resp = client.post(
            '/auth/login',
            data={'email': 'admin@classifieds.io', 'password': 'admin'},
            follow_redirects=True,
        )
        results['login_status'] = resp.status_code
        results['login_contains'] = b"Logged in successfully" in resp.data

        # 1) Reserved name: 'admin'
        resp = client.post(
            '/admin/categories/new',
            data={'name': 'admin', 'parent_id': '0', 'submit': 'Save'},
            follow_redirects=True,
        )
        results['reserved_status'] = resp.status_code
        results['reserved_flash'] = b"conflicts with system routes" in resp.data
        results['reserved_created'] = Category.query.filter_by(url_name='admin').count()

        # 2) Empty-slug: '_____'
        resp = client.post(
            '/admin/categories/new',
            data={'name': '_____', 'parent_id': '0', 'submit': 'Save'},
            follow_redirects=True,
        )
        results['empty_status'] = resp.status_code
        results['empty_flash'] = b"empty URL segment" in resp.data
        results['empty_created'] = Category.query.filter_by(url_name='').count()

        # 3) Valid pt-BR: 'Eletrônicos' -> 'eletronicos'
        resp = client.post(
            '/admin/categories/new',
            data={'name': 'Eletrônicos', 'parent_id': '0', 'submit': 'Save'},
            follow_redirects=True,
        )
        results['valid_status'] = resp.status_code
        results['valid_flash'] = b"Category created." in resp.data
        results['valid_created'] = Category.query.filter_by(
            url_name='eletronicos'
        ).count()

    return results


if __name__ == "__main__":
    out = run_tests()
    print(out)
