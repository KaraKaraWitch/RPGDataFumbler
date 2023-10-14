import pathlib

import orjson


def resolve_file(file_url: pathlib.Path, config: dict):
    content = orjson.loads(file_url.read_bytes())
    # print("[Check]", file_url.name)
    if isinstance(content, list):
        if len(content) < 2:
            return None
        item = content[1]
        actor_tests = ["characterIndex", "characterName", "name", "note", "profile"]
        weapon_tests = ["description", "name", "note"]
        # event_tests = ["characterIndex", "characterName", "name", "note", "profile"]
        if sum([act_test in actor_tests for act_test in item]) == len(actor_tests):
            return ActorMVFungler(file_url, config)
        if (
            sum([weapon_test in weapon_tests for weapon_test in item])
            == len(weapon_tests)
            and "weapon" in file_url.name.lower()
        ):
            return ItemMVFungler(file_url, config)
        if (
            sum([weapon_test in weapon_tests for weapon_test in item])
            == len(weapon_tests)
            and "item" in file_url.name.lower()
        ):
            return ItemMVFungler(file_url, config)
        if (
            sum([weapon_test in weapon_tests for weapon_test in item])
            == len(weapon_tests)
            and "armors" in file_url.name.lower()
        ):
            return ItemMVFungler(file_url, config)
        if "commonevents" in file_url.name.lower():
            return CommonEventMVFungler(file_url, config)

        # else:
        #     print()
    elif isinstance(content, dict):
        if "Map" in file_url.name and content.get("events"):
            return MapsMVFungler(file_url, config)
        if content.get("armorTypes"):
            return SystemMVfungler(file_url, config)
    # Events stuff
