import re
from pathlib import Path

import tomllib
from dotenv import dotenv_values
from samba.auth import system_session
from samba.credentials import Credentials
from samba.param import LoadParm
from samba.samdb import SamDB
import sys

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib


def read_config():
    # Load .env file
    env_vars = dotenv_values(".env")

    path = Path("config.toml")

    if not path.is_file():
        raise Exception(
            f"No configuration file found! Add your configuration to {
                str(path.absolute())}"
        )
    config_str = ""
    with open(path, "r") as f:
        for line in f:
            # Replace environment variables in the line
            for key in env_vars.keys():
                line = re.sub("\\$\\{?" + key + "\\}?", env_vars[key], line)

            config_str += line

    config = tomllib.loads(config_str)

    return config


config = read_config()

departmentlist = config.get("departmentlist", [])

afsserverlist = []
afsserverdict = config.get("afsserver", {})
for i in afsserverdict:
    for x in afsserverdict[i]:
        afsserverlist.append(i + ":" + x)
