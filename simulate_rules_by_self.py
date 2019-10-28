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

group_changes = re.compile(r"\\\$\\{(\d+):[a-zA-Z_]+\\}")
group_changes2 = re.compile(r"\$\{(\d+):[a-zA-Z_]+\}")
consequent_newline = re.compile(r"(\".+\\)(n.*\")")

def get_projects(path):
    with open(path, "r") as json_file:
        projects = json.load(json_file)
        return list(projects)

if "projects_path" in config:
    projects = get_projects(config["projects_path"])
else:
    projects = config["projects"]

repos = [x["repo"] for x in projects]

validate_projects = config.get("applied_projects", [])

learn_from = "pulls" if "pull" in config["learn_from"] else "master"

# group_changes = re.compile(r"\\\$\\{(\d+):[a-zA-Z_]+\\}")

change_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + ".json"
            for x in projects]
out_files = ["data/result/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + ".csv"
            for x in projects]
changes = []
for change_file in change_files:
    print("Combine from " + change_file)
    with open(change_file, "r") as target:
        data = json.load(target)
        changes.extend(data)

def group2increment(matchobj, identifier_ids):
    tokenid = int(matchobj.group(1))
    if tokenid in identifier_ids:
        return r"(?P=token" + str(tokenid + 1) + r")"
    else:
        identifier_ids.append(tokenid)
        return r"(?P<token" + str(tokenid + 1) + r">[\w\s_]+)"

def snippet2Regex(snippet):
    identifier_ids = []
    joinedCondition = re.escape("\n".join(snippet))
    joinedCondition = group_changes.sub(lambda m: group2increment(m, identifier_ids), joinedCondition)
    try:
        return re.compile(joinedCondition)
    except:
        exit()

def consequent2regex(matchobj, identifier_ids):
    tokenid = int(matchobj.group(1))
    return r"\g<token" + str(tokenid + 1) +r">"

def snippet2RegexConsequent(snippet):
    identifier_ids = []
    joinedCondition = "\n".join(snippet)
    # joinedCondition = consequent_newline.sub(r"\g<1>\\\g<2>", joinedCondition)
    return group_changes2.sub(lambda m: consequent2regex(m, identifier_ids), joinedCondition)

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
    tmp_rules = [x for x in rules if x["re_condition"].search(buggy)]
    if len(tmp_rules) == 0:
        return [], None
    else:
        try:
            return [x["re_condition"].sub(x["re_consequent"], buggy) for x in tmp_rules], tmp_rules
        except:
            return [], None

def getDefectKind():
    pass

output = []

out_name = change_files[0]
with open(out_name, "r") as jsonfile:
    target_changes = json.load(jsonfile)
changes_size = len(target_changes)

for i, bug in enumerate(target_changes):
    target_changes[i]["re_condition"] = snippet2RegexCondition(bug["condition"])
    target_changes[i]["re_consequent"] = snippet2RegexConsequent(bug["consequent"])
    target_changes[i]["condition"] = snippet2Realcode(bug["condition"], bug["abstracted"])
    target_changes[i]["consequent"] = snippet2Realcode(bug["consequent"], bug["abstracted"]).strip()
    target_changes[i]["created_at"] = dt.strptime(bug["created_at"],"%Y-%m-%d %H:%M:%S")

adopt_same_data = True
if adopt_same_data:
    all_changes = target_changes.copy()
else:
    with open(out_name, "r") as jsonfile:
        all_changes = json.load(jsonfile)
    changes_size = len(all_changes)

    for i, bug in enumerate(all_changes):
        all_changes[i]["re_condition"] = snippet2RegexCondition(bug["condition"])
        all_changes[i]["re_consequent"] = snippet2RegexConsequent(bug["consequent"])
        all_changes[i]["condition"] = snippet2Realcode(bug["condition"], bug["abstracted"])
        all_changes[i]["consequent"] = snippet2Realcode(bug["consequent"], bug["abstracted"]).strip()
        all_changes[i]["created_at"] = dt.strptime(bug["created_at"],"%Y-%m-%d %H:%M:%S")


for i, change in enumerate(all_changes):
    sys.stdout.write("\r%d / %d rules are collected" %
                    (i + 1, changes_size))
    tmp_change = change
    if i == 2469:
        continue

    learned_change = [x for x in target_changes if x["created_at"] < change["created_at"]]
    fixed_contents, _ = buggy2accepted(change["condition"], learned_change, 0)

    output.append({
        "sha": change["sha"],
        "learned_num": len(learned_change),
        "suggested_num": len(fixed_contents),
        "success": any([x.strip() == change["consequent"] for x in fixed_contents])
    })

OUT_TOKEN_NAME = out_files[0]
with open(OUT_TOKEN_NAME, "w") as target:
    print("Success to validate the changes Output is " + OUT_TOKEN_NAME)
    writer = csv.DictWriter(target, ["sha", "learned_num", "suggested_num", "success"])
    writer.writeheader()
    writer.writerows(output)