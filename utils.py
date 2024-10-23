import tomllib
from pathlib import Path
from dotenv import dotenv_values
import re


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
