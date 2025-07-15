# Copyright (c) 2025 Fernando "ferabreu" Mees Abreu
#
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
#
"""
This code was written and annotated by GitHub Copilot at the request of Fernando "ferabreu" Mees Abreu (https://github.com/ferabreu).

LDAP authentication support.
"""

from ldap3 import ALL, Connection, NTLM, Server
from .config import Config

def authenticate_with_ldap(email, password):
    ldap_server = Config.LDAP_SERVER
    ldap_domain = Config.LDAP_DOMAIN
    if not ldap_server or not ldap_domain:
        return False
    username = email.split('@')[0]
    user = f"{ldap_domain}\\{username}"
    server = Server(ldap_server, get_info=ALL)
    try:
        conn = Connection(server, user=user, password=password, authentication=NTLM, auto_bind=True)
        conn.unbind()
        return True
    except Exception:
        return False