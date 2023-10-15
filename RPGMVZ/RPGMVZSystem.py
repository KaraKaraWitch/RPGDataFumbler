import pathlib
import typing

import orjson
from .RPGMVZBase import MVZFungler

# Common Terms used for quick patches.
# Reduces work required to translate stuff.
terms_patch = {
    "basic": {
        "レベル": "Level",
        "Lv": "Lv",
        "ＨＰ": "HP",
        "HP": "HP",
        "ＭＰ": "MP",
        "MP": "MP",
        "ＴＰ": "TP",
        "TP": "TP",
        "経験値": "EXP",
        "EXP": "EXP",
    },
    "commands": {
        "戦う": "Fight",
        "逃げる": "Escape",
        "攻撃": "Attack",
        "防御": "Guard",
        "アイテム": "Item",
        "スキル": "Skill",
        "装備": "Equip",
        "ステータス": "Status",
        "並び替え": "Formation",
        "セーブ": "Save",
        "ゲーム終了": "End Game",
        "オプション": "Options",
        "武器": "Weapon",
        "防具": "Armor",
        "大事なもの": "Key Item",
        "装備": "Equip",
        "最強装備": "Optimize",
        "全て外す": "Clear",
        "ニューゲーム": "New Game",
        "コンティニュー": "Continue",
        #
        "タイトルへ": "To Title",
        "やめる": "Cancel",
        #
        "購入する": "Buy",
        "売却する": "Sell",
    },
    "params": {
        "最大ＨＰ": "Max HP",
        "最大ＭＰ": "Max MP",
        "攻撃力": "Attack",
        "防御力": "Defense",
        "魔法力": "M. Attack",
        "魔法防御": "M. Defense",
        "敏捷性": "Agility",
        "運": "Luck",
        "命中率": "Hit",
        "回避率": "Evasion",
    },
    "messages": {
        "actionFailure": ["%1には効かなかった！", "There was no effect on %1!"],
        "actorDamage": ["%1は %2 のダメージを受けた！", "%1 took %2 damage!"],
        "actorDrain": ["%1は%2を %3 奪われた！", "%1 was drained of %2 %3!"],
        "actorGain": ["%1の%2が %3 増えた！", "%1 gained %2 %3!"],
        "actorLoss": ["%1の%2が %3 減った！", "%1 lost %2 %3!"],
        "actorNoDamage": ["%1はダメージを受けていない！", "%1 took no damage!"],
        "actorNoHit": ["ミス！　%1はダメージを受けていない！", "Miss! %1 took no damage!"],
        "actorRecovery": ["%1の%2が %3 回復した！", "%1 recovered %2 %3!"],
        "alwaysDash": ["常時ダッシュ", "Always Dash"],
        "bgmVolume": ["BGM 音量", "BGM Volume"],
        "bgsVolume": ["BGS 音量", "BGS Volume"],
        "buffAdd": ["%1の%2が上がった！", "%1's %2 went up!"],
        "buffRemove": ["%1の%2が元に戻った！", "%1's %2 returned to normal!"],
        "commandRemember": ["コマンド記憶", "Remember Command"],
        "counterAttack": ["%1の反撃！", "%1 counterattacked!"],
        "criticalToActor": ["痛恨の一撃！！", "A painful blow!!"],
        "criticalToEnemy": ["会心の一撃！！", "An critical hit!!"],
        "debuffAdd": ["%1の%2が下がった！", "%1's %2 went down!"],
        "defeat": ["%1は戦いに敗れた。", "%1 was defeated."],
        "emerge": ["%1が出現！", "%1 emerged!"],
        "enemyDamage": ["%1に %2 のダメージを与えた！", "%1 took %2 damage!"],
        "enemyDrain": ["%1の%2を %3 奪った！", "%1 was drained of %2 %3!"],
        "enemyGain": ["%1の%2が %3 増えた！", "%1 gained %2 %3!"],
        "enemyLoss": [
            "%1の%2が %3 減った！",
            "%1 lost %2 %3!",
        ],
        "enemyNoDamage": ["%1にダメージを与えられない！", "%1 took no damage!"],
        "enemyNoHit": ["ミス！　%1にダメージを与えられない！", "Miss! %1 took no damage!"],
        "enemyRecovery": ["%1の%2が %3 回復した！", "%1 recovered %2 %3!"],
        "escapeFailure": ["しかし逃げることはできなかった！", "However, it was unable to escape!"],
        "escapeStart": ["%1は逃げ出した！", "%1 has started to escape!"],
        "evasion": ["%1は攻撃をかわした！", "%1 evaded the attack!"],
        "expNext": ["次の%1まで", "To Next %1"],
        "expTotal": ["現在の%1", "Current %1"],
        "file": ["ファイル", "File"],
        "levelUp": ["%1は%2 %3 に上がった！", "%1 is now %2 %3!"],
        "loadMessage": ["どのファイルをロードしますか？", "Load which file?"],
        "magicEvasion": ["%1は魔法を打ち消した！", "%1 nullified the magic!"],
        "magicReflection": ["%1は魔法を跳ね返した！", "%1 reflected the magic!"],
        "meVolume": ["ME 音量", "ME Volume"],
        "obtainExp": ["%1 の%2を獲得！", "%1 %2 received!"],
        "obtainGold": ["お金を %1\\G 手に入れた！", "%1\\G found!"],
        "obtainItem": ["%1を手に入れた！", "%1 found!"],
        "obtainSkill": ["%1を覚えた！", "%1 learned!"],
        "partyName": ["%1たち", "%1's Party"],
        "possession": ["持っている数", "Possession"],
        "preemptive": ["%1は先手を取った！", "%1 got the upper hand!"],
        "saveMessage": ["どのファイルにセーブしますか？", "Save to which file?"],
        "seVolume": ["SE 音量", "SE Volume"],
        "substitute": ["%1が%2をかばった！", "%1 protected %2!"],
        "surprise": ["%1は不意をつかれた！", "%1 was surprised!"],
        "useItem": ["%1は%2を使った！", "%1 uses %2!"],
        "victory": ["%1の勝利！", "%1 was victorious!"],
    },
}


class SystemMVfungler(MVZFungler):

    fungler_type = "system"

    def create_maps(self):
        self.read_mapped(create=True)
        mapping: typing.Dict[str, typing.Any] = {"type": self.fungler_type}
        system_data = self.original_data
        if not isinstance(system_data, dict):
            raise Exception("System not in right format.")
        if self.config["System"]["armor_types"]:
            mapping["armor_types"] = []
            for idx, armor in enumerate(system_data["armorTypes"]):
                if armor:
                    mapping["armor_types"].append([idx, armor])
        if self.config["System"]["equip_types"]:
            mapping["equip_types"] = []
            for idx, equip in enumerate(system_data["equipTypes"]):
                if equip:
                    mapping["equip_types"].append([idx, equip])
        if self.config["System"]["skill_types"]:
            mapping["skill_types"] = []
            for idx, skill in enumerate(system_data["skillTypes"]):
                if skill:
                    mapping["skill_types"].append([idx, skill])
        if self.config["System"]["terms"]:
            mapping["terms"] = system_data["terms"]
            terms = terms_patch["basic"]
            for k, v in enumerate(mapping["terms"]["basic"]):
                if v in terms:
                    self.logger.info(
                        f'[SystemCommon|Basic] Found common term for: {mapping["terms"]["basic"][k]}'
                    )
                    mapping["terms"]["basic"][k] = terms[v]
            terms = terms_patch["commands"]
            for k, v in enumerate(mapping["terms"]["commands"]):
                if v in terms:
                    self.logger.info(
                        f'[SystemCommon|Commands] Found common term for: {mapping["terms"]["commands"][k]}'
                    )
                    mapping["terms"]["commands"][k] = terms[v]
            terms = terms_patch["params"]
            for k, v in enumerate(mapping["terms"]["params"]):
                if v in terms:
                    self.logger.info(
                        f'[SystemCommon|Params] Found common term for: {mapping["terms"]["params"][k]}'
                    )
                    mapping["terms"]["params"][k] = terms[v]
            terms = terms_patch["messages"]
            for k, v in mapping["terms"]["messages"].items():
                if v == terms.get(k, ["", ""])[0]:
                    self.logger.info(
                        f'[SystemCommon|Messages] Found common term for: {mapping["terms"]["messages"][k]}'
                    )
                    mapping["terms"]["messages"][k] = terms.get(k, ["", ""])[1]
        mapping["game_title"] = system_data["gameTitle"]
        self.mapped_file.write_bytes(orjson.dumps(mapping, option=orjson.OPT_INDENT_2))

    def apply_maps(self):
        mapping = self.read_mapped()
        if not mapping:
            return
        system_data = self.original_data
        if not isinstance(system_data, dict):
            raise Exception("System not in right format.")
        if self.config["System"]["armor_types"]:
            for idx, value in mapping["armor_types"]:
                system_data["armorTypes"][idx] = value
        if self.config["System"]["equip_types"]:
            for idx, value in mapping["equip_types"]:
                system_data["equipTypes"][idx] = value
        if self.config["System"]["skill_types"]:
            for idx, value in mapping["skill_types"]:
                system_data["skillTypes"][idx] = value
        if self.config["System"]["terms"]:
            system_data["terms"] = mapping["terms"]
        system_data["gameTitle"] = mapping["game_title"]
        self.original_file.write_bytes(orjson.dumps(system_data))
