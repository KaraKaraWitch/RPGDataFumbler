import logging
import pathlib
import shutil
import typing
import orjson


class RubyHandler:
    def __init__(
        self, game_file: pathlib.Path, config: dict, project_name: str = "tl_workspace"
    ):
        self.config = config
        self.game_file = game_file
        self.project_name = project_name
        self.game_type = self.config["General"].get("type", "MV")
        self.logger = logging.getLogger("Ruby|Handler")
        self._project_folders: typing.Optional[typing.Dict] = None
        if self.game_type != "Ruby":
            raise Exception("Game type must be `Ruby`.")

    