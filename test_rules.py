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

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]


CHANGE_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + ".json"
OUT_TOKEN_NAME2 = "data/changes/" + owner + "_" + repo + "_" + lang + "2.json"


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
        return  r"(P=token" + str(tokenid + 1) + r"(\$\d+|\w+))"
    else:
        identifier_ids.append(tokenid)
        return r"(?P<token" + str(tokenid + 1) + r">(\$\d+|\w+))"

def snippet2Regex(snippet):
    identifier_ids = []
    joinedCondition = snippet[0] if len(snippet) < 2 else "\n".join(snippet)
    joinedCondition = re.escape(joinedCondition)
    joinedCondition = re.sub(r"\\\$(\d+)" , lambda m: group2increment(m, identifier_ids), joinedCondition)
    return re.compile(joinedCondition)


clone_target_repo()
target_repo = git.Repo("data/repos/" + repo)

with open(CHANGE_JSON_NAME, "r") as json_file:
    changes = json.load(json_file)

output = []
changes_len = len(changes)
head_commit = target_repo.commit("HEAD")

total_condition = 0
total_frequency = 0

for i, change in enumerate(changes[:-1]):
    if len(change["condition"]) == 0 or len(change["consequent"]) == 0:
        continue
    sys.stdout.write("\r%d / %d pulls %d rules are collected" %
                    (i + 1, changes_len, len(output)))
    token_dict = change

    re_condition = snippet2Regex(change["condition"])
    re_consequent = snippet2Regex(change["consequent"])
    condition_change = [x for x in changes[i+1:]
                        if re_condition.search("\n".join(x["condition"])) and x["number"] != change["number"]]
    if len(condition_change) == 0:
        continue
    consequent_change = [x["number"] for x in condition_change if re_consequent.search("\n".join(x["consequent"]))]

    token_dict["successed_number"] = list(set(consequent_change))
    token_dict["failed_number"] = list(set([x["number"] for x in condition_change
                                            if x["number"] not in token_dict["successed_number"]]))
    if len(token_dict["failed_number"]) > 0:
        token_dict["successed_number"] = [x for x in token_dict["successed_number"]
                                        if x < min(token_dict["failed_number"])]
        token_dict["failed_number"] = [token_dict["failed_number"][0]]

    token_dict["frequency"] = len(token_dict["successed_number"])
    token_dict["accuracy"] = token_dict["frequency"] / (token_dict["frequency"] + len(token_dict["failed_number"]))

    total_condition += token_dict["frequency"] + len(token_dict["failed_number"])
    total_frequency += token_dict["frequency"]

    output.append(token_dict)

output = sorted(output, key=lambda x: x["accuracy"], reverse=True)

print("output %d rules" % len(output))
if total_condition == 0:
    print("Total condition: %d\nTotal frequency: %d" 
        % (total_condition, total_frequency))
else:
    print("Total condition: %d\nTotal frequency: %d\nTotal accuracy %f" 
        % (total_condition, total_frequency, total_frequency / total_condition))
with open(OUT_TOKEN_NAME2, "w") as target:
    json.dump(output, target, indent=2)
