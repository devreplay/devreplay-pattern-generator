from json import dump, load
from configparser import ConfigParser
from difflib import ndiff
from prefixspan import PrefixSpan_frequent, PrefixSpan_topk,PrefixSpan
from functools import reduce

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]
rule_method = config["Rule"]["frequent_or_topk"]
thresholds = [int(x) for x in config["Rule"]["thresholds"].split()]

INPUT_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + ".json"
OUT_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + "2.json"

def remove_dup_changes(changes_sets):
    new_changes = []
    current_changes = []
    current_pull = 0
    changes_sets = [x for x in changes_sets if any([y.startswith("*") for y in x["changes_set"]])]
    for changes_set in changes_sets:
        changes_set["changes_set"] = list(set([x for x in changes_set["changes_set"] if not x.startswith("=")]))
        if current_pull == changes_set["number"]:
            if changes_set["changes_set"] in current_changes:
                continue
            else:
                new_changes[-1]["changes_set"].extend(changes_set["changes_set"])
                current_changes.append(changes_set["changes_set"])
        else:
                current_changes = []
                new_changes.append(changes_set)
                current_changes.append(changes_set["changes_set"])
        current_pull = changes_set["number"]
    return new_changes


with open(INPUT_JSON_NAME, mode='r', encoding='utf-8') as f:
    changes_sets = load(f)

changes = remove_dup_changes(changes_sets)


with open(OUT_JSON_NAME, mode='w', encoding='utf-8') as f:
    dump(changes, f, indent=1)
