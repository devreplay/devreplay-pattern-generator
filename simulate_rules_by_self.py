import os
import git
import json
import csv
import re
import sys
from collections import defaultdict
from datetime import datetime as dt
from datetime import timedelta
from devreplay_simulate_util import snippet2RegexCondition, consequent2regex, buggy2accepted_id, snippet2RegexConsequent, snippet2Realcode

with open("config.json", "r") as json_file:
    config = json.load(json_file)

lang = config["lang"]

def get_projects(path):
    with open(path, "r") as json_file:
        projects = json.load(json_file)
        return [x for x in list(projects) if "language" not in x or x["language"] == lang]


if "projects_path" in config:
    projects = get_projects(config["projects_path"])
else:
    projects = config["projects"]

learn_from = "pulls" if "pull" in config["learn_from"] else "master"
validate_by = "pulls" if "pull" in config["validate_by"] else "master"
change_files = {x["repo"]: "data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang + "_" + validate_by + ".json"
                for x in projects}

rule_files = {x["repo"]: "data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang + "_" + learn_from + ".json"
              for x in projects}

from_self = True

if from_self:
    out_files = {x["repo"]: "data/result/" + x["owner"] + "_" + x["repo"] + "_" + lang + "_" + validate_by
                 for x in projects}
else:
    out_files = {x["repo"]: "data/result/" + x["owner"] + "_" + x["repo"] + "_" + lang + "_" + validate_by + "_cross"
                 for x in projects}

projects_patterns = {}

print("collecting rules")
for repo, out_name in rule_files.items():

    with open(out_name, "r") as jsonfile:
        target_changes = json.load(jsonfile)
    patterns = []

    prev_sha = ""
    sha_count = 0
    for bug in target_changes:
        # if len(bug["condition"]) > 5 or len(bug["consequent"]) > 5:
        #     continue
        sha = bug["sha"]
        sha_count = sha_count + 1 if sha == prev_sha else 0
        prev_sha = sha
        sha += f"_{str(sha_count)}"
        try:
            patterns.append({
                "sha": sha,
                "re_condition": snippet2RegexCondition(bug["condition"]),
                "re_consequent": snippet2RegexConsequent(bug["consequent"]),
                "condition": snippet2Realcode(bug["condition"], bug["abstracted"]),
                "consequent": snippet2Realcode(bug["consequent"], bug["abstracted"]).strip(),
                "created_at": dt.strptime(bug["created_at"], "%Y-%m-%d %H:%M:%S")
            })
        except KeyError as e:
            print(e)
            continue
    projects_patterns[repo] = patterns

projects_changes = {}

print("collecting changes")
if learn_from != validate_by:
    for repo, out_name in change_files.items():
        with open(out_name, "r") as jsonfile:
            target_changes = json.load(jsonfile)
        patterns = []

        for bug in target_changes:
            try:
                patterns.append({
                    "sha": bug["sha"],
                    "condition": snippet2Realcode(bug["condition"], bug["abstracted"]),
                    "consequent": snippet2Realcode(bug["consequent"], bug["abstracted"]).strip(),
                    "created_at": dt.strptime(bug["created_at"], "%Y-%m-%d %H:%M:%S")
                })
            except KeyError as e:
                print(e)
                continue
        projects_changes[repo] = patterns
else:
    projects_changes = projects_patterns


for repo in change_files.keys():

    all_changes = projects_changes[repo].copy()
    if not from_self:
        learned_changes2 = []
        for repo2 in change_files.keys():
            if repo2 != repo:
                learned_changes2.extend(projects_patterns[repo2])

    changes_size = len(all_changes)

    days_span = [1, 7, 30]
    failed_sha = defaultdict(list)
    for days in days_span:
        sys.stdout.write("\r%s / %d days patterns are collecting" %
                    (repo, days))
        
        OUT_TOKEN_NAME = out_files[repo] + f"_{days}.csv"
        with open(OUT_TOKEN_NAME, "w") as target:
            print("Success to validate the changes Output is " + OUT_TOKEN_NAME)
            writer = csv.DictWriter(target, ["sha", "learned_num", "suggested_num", "success", "rule_index", "reffered_sha"])
            writer.writeheader()
            for i, change in enumerate(all_changes):
                if i % 100 == 0:
                    sys.stdout.write("\r%d / %d patterns are collected" %
                                    (i + 1, changes_size))
                period_date = change["created_at"] - timedelta(days=days)
                learned_change = [x for x in projects_patterns[repo]
                                if x["created_at"] < change["created_at"] and\
                                    x["created_at"] > period_date and \
                                    x["sha"] not in failed_sha[days]]
                if not from_self:
                    learned_change.extend(learned_changes2)
                fixed_contents = buggy2accepted_id(change["condition"], learned_change, 0)

                success_index = [i for i, x in enumerate(fixed_contents) if x[0] == change["consequent"]]
                failed_sha[days].extend([x[1] for x in fixed_contents if x[0] != change["consequent"]])

                output = {
                    "sha": change["sha"],
                    "learned_num": len(learned_change),
                    "suggested_num": len(fixed_contents),
                    "rule_index": min(success_index) + 1 if len(success_index) != 0 else -1,
                    "success": len(success_index) != 0,
                    "reffered_sha": fixed_contents[min(success_index)][1] if len(success_index) != 0 else "Nothing"
                }

                writer.writerow(output)
