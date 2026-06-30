from typing import Any
from pathlib import Path
from endstone.plugin import Plugin
from pydantic import BaseModel
from ruamel.yaml import YAML, CommentedMap
import os
from endstone import Logger

class Config(BaseModel):
    streamlabs_socket_token: str = ""
    log_events: bool = False

def load_config(plugin: Plugin) -> Config:
    folder = Path(plugin.data_folder)
    folder.mkdir(parents=True, exist_ok=True)
    cfg_path = folder / "config.yaml"
    logger = plugin.logger

    yml = YAML()
    yml.version = (1, 2)
    yml.preserve_quotes = False

    defaults: dict[str, tuple[Any, str]] = {
        "streamlabs_socket_token": ("", "\"Your Socket API Token\" from https://streamlabs.com/dashboard#/settings/api-settings. You can also do this through environment variable (STREAMLABS_SOCKET_TOKEN), if perferred."),
        # "log_events" is less scary than "debug," people shouldn't be afraid of using this
        "log_events": (False, "Log events by sending DEBUG messages. This will also set the log level to DEBUG, which may fill up the console with a lot of stuff. You can also do this through environment variable (DEBUG=1) if perferred."),
    }

    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            existing = yml.load(f)
        if not isinstance(existing, CommentedMap):
            existing = CommentedMap(existing or {})
    else:
        existing = CommentedMap()

    for key, (value, comment) in defaults.items():
        keys = key.split(".")
        current = existing

        for i, k in enumerate(keys[:-1]):
            if k not in current:
                current[k] = CommentedMap()
            current = current[k]

        if keys[-1] not in current:
            current[keys[-1]] = value
            current.yaml_add_eol_comment(comment, keys[-1])

    with open(cfg_path, "w", encoding="utf-8") as f:
        yml.dump(existing, f)

    def commented_map_to_dict(data: Any) -> Any:
        if isinstance(data, CommentedMap):
            return {k: commented_map_to_dict(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [commented_map_to_dict(v) for v in data]
        return data

    config_dict = commented_map_to_dict(existing)

    streamlabs_socket_token_env = os.environ.get("STREAMLABS_SOCKET_TOKEN")
    if streamlabs_socket_token_env:
        config_dict["streamlabs_socket_token"] = streamlabs_socket_token_env
        logger.warning("streamlabs_socket_token was overridden by environment variable")

    debug_env = os.environ.get("DEBUG", "").lower()
    if debug_env not in ("", "0", "false"):
        config_dict["log_events"] = True
    else:
        if debug_env != "":
            config_dict["log_events"] = False
    if debug_env != "":
        logger.warning(f"log_events was overridden to `{config_dict['log_events']}` by environment variable")

    return Config(**config_dict)