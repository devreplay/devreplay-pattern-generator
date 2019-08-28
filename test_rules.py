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
    joinedCondition = group_changes.sub(lambda m: group2increment(m, identifier_ids), joinedCondition)
    return re.compile(joinedCondition)


with open("config.json", "r") as json_file:
    config = json.load(json_file)

lang = config["lang"]
projects = config["projects"]
learn_from = "pulls" if "pull" in config["learn_from"] else "master"
validate_by = "pulls" if "pull" in config["validate_by"] else "master"
test_target = r"(\${?(\d+)(:[a-zA-Z_]+})?))" if validate_by == "pulls" else r"[a-zA-Z_]+)"
group_changes = re.compile(r"\\\$\\?{?(\d+)(:[a-zA-Z_]+\\})?")

change_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + ".json"
            for x in projects]
changes = []
for change_file in change_files:
    print("Combine from " + change_file)
    with open(change_file, "r") as target:
        data = json.load(target)
        changes.extend(data)

if learn_from != validate_by:
    validate_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + validate_by + ".json"
            for x in projects]
    validates = []
    for validate_file in validate_files:
        print("Combine from " + validate_file)
        with open(validate_file, "r") as target:
            data = json.load(target)
            validates.extend(data)
else:
    validates = changes
contents = "number" if "pull" in validate_by else "sha"
target_len = len(validates)

output = []
changes_len = len(changes)

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

    date = dt.strptime(change["created_at"],"%Y-%m-%d %H:%M:%S")
    condition_change = [x for x in validates
                        if re_condition.search("\n".join(x["condition"]))
                        and dt.strptime(x["created_at"],"%Y-%m-%d %H:%M:%S") > date]

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
    print("Total condition: %d\nTotal frequency: %d\nTotal accuracy: %f\nCoveradge: %f" 
        % (total_condition, total_frequency, total_frequency / total_condition, total_frequency/target_len))


if len(projects) == 1:
    OUT_TOKEN_NAME = "data/changes/" + projects[0]["owner"] + "_" + projects[0]["repo"] + \
    "_" + lang + "_" + learn_from + "_validated.json"
else:
    OUT_TOKEN_NAME = "data/changes/devreplay.json"

with open(OUT_TOKEN_NAME, "w") as target:
    print("Success to validate the changes Output is " + OUT_TOKEN_NAME)
    json.dump(output, target, indent=2)
