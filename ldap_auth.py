from config import Config
from ldap3 import Server, Connection, NTLM, ALL

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