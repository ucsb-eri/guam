from samba.auth import system_session
from samba.credentials import Credentials
from samba.param import LoadParm
from samba.samdb import SamDB

from guam.config import config


def connect():
    server_config = config.get("ldap", {})

    lp = LoadParm()
    creds = Credentials()
    creds.guess(lp)
    creds.set_username(server_config.get("username", ""))
    creds.set_password(server_config.get("password", ""))
    samdb = SamDB(
        url=server_config.get("url", ""),
        session_info=system_session(),
        credentials=creds,
        lp=lp,
    )
    return samdb
