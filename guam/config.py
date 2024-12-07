import logging
import os
import sys

from xdg_base_dirs import xdg_config_home

if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

logger = logging.getLogger("uvicorn.error")


def read_config():
    # config = {"USER": "foo", "EMAIL": "foo@example.org"}
    system_config = os.path.join("/", "etc", "guam", "config.toml")
    user_config = os.path.join(xdg_config_home(), "guam", "config.toml")
    config_path = user_config if os.path.exists(user_config) else system_config

    try:
        f = open(config_path, "rb")
        config = tomllib.load(f)

        return config
    except FileNotFoundError:
        logger.error(
            f"""No configuration found!

For system config, create: {system_config}
For user config, create: {user_config}
"""
        )
        exit(1)
    except tomllib.TOMLDecodeError:
        logger.error(f"Config is  invalid. Edit: {config_path}")
        exit(1)


config = read_config()

departmentlist = config.get("departmentlist", [])

afsserverlist = []
afsserverdict = config.get("afsserver", {})
for i in afsserverdict:
    for x in afsserverdict[i]:
        afsserverlist.append(i + ":" + x)
