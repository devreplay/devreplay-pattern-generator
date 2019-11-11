import os
import git
import json
import csv
import re
import sys
from pathlib import Path
from lang_extentions import lang_extentions
from collections import defaultdict
from datetime import datetime as dt

with open("config.json", "r") as json_file:
    config = json.load(json_file)

lang = config["lang"]

group_changes2 = re.compile(r"\$\{(\d+):[a-zA-Z_]+\}")
consequent_newline = re.compile(r"(\".+\\)(n.*\")")

def get_projects(path):
    with open(path, "r") as json_file:
        projects = json.load(json_file)
        return [x for x in list(projects) if "language" not in x or x["language"] == lang]

if "projects_path" in config:
    projects = get_projects(config["projects_path"])
else:
    projects = config["projects"]

learn_from = "pulls" if "pull" in config["learn_from"] else "master"

# group_changes = re.compile(r"\\\$\\{(\d+):[a-zA-Z_]+\\}")

change_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + ".json"
            for x in projects]

from_self = False

if from_self:
    out_files = ["data/result/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + ".csv"
                for x in projects]
else:
    out_files = ["data/result/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + "_cross.csv"
                for x in projects]
def group2increment(matchobj, identifier_ids):
    tokenid = int(matchobj.group(1))
    if tokenid in identifier_ids:
        return r"(?P=token" + str(tokenid + 1) + r")"
    else:
        identifier_ids.append(tokenid)
        return r"(?P<token" + str(tokenid + 1) + r">[\w\s_]+)"

def consequent2regex(matchobj, identifier_ids):
    tokenid = int(matchobj.group(1))
    return r"\g<token" + str(tokenid + 1) +r">"

def snippet2RegexConsequent(snippet):
    identifier_ids = []
    joinedCondition = "\n".join(snippet)
    # joinedCondition = consequent_newline.sub(r"\g<1>\\\g<2>", joinedCondition)
    return group_changes2.sub(lambda m: consequent2regex(m, identifier_ids), joinedCondition)

group_changes = re.compile(r"\\\$\\{(\d+):[a-zA-Z_]+\\}")
def snippet2RegexCondition(snippet):
    identifier_ids = []
    joinedCondition = "\n".join(snippet)
    joinedCondition = re.escape(joinedCondition)
    joinedCondition = group_changes.sub(lambda m: group2increment(m, identifier_ids), joinedCondition)
    try:
        return re.compile(joinedCondition)
    except:
        exit()

def snippet2Realcode(snippet, abstracted):
    return group_changes2.sub(lambda m: abstracted[m.group(1)], "\n".join(snippet))
    

def clone_target_repo(owner, repo):
    data_repo_dir = "data/repos"
    if not os.path.exists(data_repo_dir + "/" + repo):
        if not os.path.exists(data_repo_dir):
            os.makedirs(data_repo_dir)
        print("Cloning " + data_repo_dir + "/" + repo)
        if "github_token" in config:
            git_url = "https://" + config["github_token"] + ":@github.com/" + owner + "/" + repo +".git"
        else:
            git_url = "https://github.com/" + owner + "/" + repo +".git"
        git.Git(data_repo_dir).clone(git_url)
    else:
        pass

def buggy2accepted(buggy, rules, rule_size):
    suggested_rules = [x for x in rules if x["re_condition"].search(buggy)]
    if len(suggested_rules) == 0:
        return [], None
    else:
        try:
            return [x["re_condition"].sub(x["re_consequent"], buggy) for x in suggested_rules], suggested_rules
        except:
            return [], None



projects_patterns = {}


for change_id, out_name in enumerate(change_files):

    with open(out_name, "r") as jsonfile:
        target_changes = json.load(jsonfile)
    patterns = []

    for bug in target_changes:
        # if len(bug["condition"]) > 5 or len(bug["consequent"]) > 5:
        #     continue
        patterns.append({
            "sha": bug["sha"],
            "re_condition": snippet2RegexCondition(bug["condition"]),
            "re_consequent": snippet2RegexConsequent(bug["consequent"]),
            "condition": snippet2Realcode(bug["condition"], bug["abstracted"]),
            "consequent": snippet2Realcode(bug["consequent"], bug["abstracted"]).strip(),
            "created_at": dt.strptime(bug["created_at"],"%Y-%m-%d %H:%M:%S")
        })
    projects_patterns[out_name] = patterns



for change_id, out_name in enumerate(change_files):
    output = []

    all_changes = projects_patterns[out_name].copy()
    if not from_self:
        learned_changes2 = []
        for out_name2 in change_files:
            if out_name2 != out_name:
                learned_changes2.extend(projects_patterns[out_name2])
    
    changes_size = len(all_changes)

    for i, change in enumerate(all_changes):
        sys.stdout.write("\r%d / %d patterns are collected" %
                        (i + 1, changes_size))
        if from_self:
            learned_change = [x for x in projects_patterns[out_name] if x["created_at"] < change["created_at"]]
        else:
            learned_change = [x for x in projects_patterns[out_name] if x["created_at"] < change["created_at"]]
            learned_change.extend(learned_changes2)
            # learned_change = learned_changes2
        fixed_contents, _ = buggy2accepted(change["condition"], learned_change, 0)

        output.append({
            "sha": change["sha"],
            "learned_num": len(learned_change),
            "suggested_num": len(fixed_contents),
            "success": any([x.strip() == change["consequent"] for x in fixed_contents])
        })

    OUT_TOKEN_NAME = out_files[change_id]
    with open(OUT_TOKEN_NAME, "w") as target:
        print("Success to validate the changes Output is " + OUT_TOKEN_NAME)
        writer = csv.DictWriter(target, ["sha", "learned_num", "suggested_num", "success"])
        writer.writeheader()
        writer.writerows(output)