import sys
import os
import glob
import json
from collections import defaultdict, OrderedDict
from configparser import ConfigParser
from pathlib import Path
import git
from lang_extentions import lang_extentions
import itertools
import re
from datetime import datetime as dt

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]

learn_from = "pulls" if config["Option"].getboolean("learn_from_pulls") else "master"
validate_by = "pulls" if config["Option"].getboolean("validate_by_pulls") else "master"
test_target = r"(\${?(\d+)(:[a-zA-Z_]+})?))" if validate_by == "pulls" else r"[a-zA-Z_]+)"

CHANGE_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + "_" + learn_from +".json"
MASTER_CHANGE_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + "_" + validate_by + ".json"
OUT_TOKEN_NAME2 = "data/changes/" + owner + "_" + repo + "_" + lang + "_" + learn_from + "_validated.json"


def clone_target_repo():
    data_repo_dir = "data/repos"
    if not os.path.exists(data_repo_dir):
        os.makedirs(data_repo_dir)
    if not os.path.exists(data_repo_dir + "/" + repo):
        if "Token" in config["GitHub"]:
            git_url = "https://" + config["GitHub"]["Token"] + ":@github.com/" + owner + "/" + repo +".git"
        else:
            git_url = "https://github.com/" + owner + "/" + repo +".git"
        git.Git(data_repo_dir).clone(git_url)


def group2increment(matchobj, identifier_ids):
    tokenid = int(matchobj.group(1))
    if tokenid in identifier_ids:
        return  r"(P=token" + str(tokenid + 1) + test_target
    else:
        identifier_ids.append(tokenid)
        return r"(?P<token" + str(tokenid + 1) + r">" + test_target

def snippet2Regex(snippet):
    identifier_ids = []
    joinedCondition = "\n".join(snippet)
    joinedCondition = re.escape(joinedCondition)
    joinedCondition = re.sub(r"\\\$\\?{?(\d+)(:[a-zA-Z_]+\\})?" , lambda m: group2increment(m, identifier_ids), joinedCondition)
    return re.compile(joinedCondition)


clone_target_repo()
target_repo = git.Repo("data/repos/" + repo)

with open(CHANGE_JSON_NAME, "r") as json_file:
    changes = json.load(json_file)

if "combined_owner" in config["Option"] and "combined_repo" in config["Option"]:
    CHANGE_JSON_NAME2 = "data/changes/" + config["Option"]["combined_owner"] + "_" + config["Option"]["combined_repo"] + "_" + lang + "_" + learn_from +".json"
    with open(CHANGE_JSON_NAME2, "r") as json_file:
        changes2 = json.load(json_file)
        changes.extend(changes2)

if validate_by == "master":
    with open(MASTER_CHANGE_JSON_NAME, "r") as json_file:
        master_changes = json.load(json_file)
    date = dt.strptime(changes[-1]["created_at"],"%Y-%m-%d %H:%M:%S")
    master_changes = [x for x in master_changes
                      if date < dt.strptime(x["created_at"],"%Y-%m-%d %H:%M:%S")]
    contents = "sha"
    target_len = len(master_changes)
    print(f"# of master changes are {target_len}")
else:
    contents = "number"
    target_len = len(changes)
    print(f"# of pull changes are {target_len}")

output = []
changes_len = len(changes)
head_commit = target_repo.commit("HEAD")

total_condition = 0
total_frequency = 0
useful_lens = []
successed_numbers = []
for i, change in enumerate(reversed(changes[1:])):
    if len(change["condition"]) == 0 or len(change["consequent"]) == 0\
        or change[contents] in successed_numbers or len(change["condition"]) > 5:
        continue
    sys.stdout.write("\r%d / %d pulls %d rules are collected" %
                    (i + 1, changes_len, len(output)))
    token_dict = change

    re_condition = snippet2Regex(change["condition"])
    re_consequent = snippet2Regex(change["consequent"])

    if validate_by == "master":
        date = dt.strptime(change["created_at"],"%Y-%m-%d %H:%M:%S")
        condition_change = [x for x in master_changes
                            if re_condition.search("\n".join(x["condition"]))
                            and dt.strptime(x["created_at"],"%Y-%m-%d %H:%M:%S") > date]
    else:
        condition_change = [x for x in changes
                            if re_condition.search("\n".join(x["condition"]))
                            and x["number"] > change["number"]]
    if len(condition_change) == 0:
        continue
    consequent_change = [x[contents] for x in condition_change if re_consequent.search("\n".join(x["consequent"]))]

    token_dict["successed_number"] = list(set([x for x in consequent_change if x not in successed_numbers]))
    token_dict["failed_number"] = list(set([x[contents] for x in condition_change
                                            if x[contents] not in token_dict["successed_number"]]))

    if len(token_dict["failed_number"]) > 0:
        token_dict["successed_number"] = [x for x in token_dict["successed_number"]
                                          if x < min(token_dict["failed_number"])]
        token_dict["failed_number"] = [token_dict["failed_number"][0]]

    successed_numbers.extend(token_dict["successed_number"])
    token_dict["frequency"] = len(token_dict["successed_number"])
    token_dict["accuracy"] = token_dict["frequency"] / (token_dict["frequency"] + len(token_dict["failed_number"]))

    total_condition += token_dict["frequency"] + len(token_dict["failed_number"])
    total_frequency += token_dict["frequency"]
    if token_dict["frequency"] != 0:
        output.append(token_dict)

output = sorted(output, key=lambda x: x["accuracy"], reverse=True)

print("\noutput %d rules" % len(output))
if total_condition == 0:
    print("Total condition: %d\nTotal frequency: %d" 
        % (total_condition, total_frequency))
else:
    print("Total condition: %d\nTotal frequency: %d\nTotal accuracy: %f\nRecall: %f" 
        % (total_condition, total_frequency, total_frequency / total_condition, total_frequency/target_len))
with open(OUT_TOKEN_NAME2, "w") as target:
    json.dump(output, target, indent=2)
