import os
import git
import json
import re
import sys
from pathlib import Path
from lang_extentions import lang_extentions
from collections import defaultdict
from datetime import datetime as dt
from devreplay_simulate_util import snippet2RegexCondition
from datetime import timedelta

with open("config.json", "r") as json_file:
    config = json.load(json_file)

lang = config["lang"]


def get_projects(path):
    with open(path, "r") as json_file:
        projects = json.load(json_file)
        return list(projects)


if "projects_path" in config:
    projects = get_projects(config["projects_path"])
else:
    projects = config["projects"]

repos = [x["repo"] for x in projects]
ignore_test = config.get("ignore_test", False)

learn_from = "pulls" if "pull" in config["learn_from"] else "master"

change_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang + "_" + learn_from + ".json"
                for x in projects]
changes = []
for change_file in change_files:
    print("Combine changes from " + change_file)
    with open(change_file, "r") as target:
        data = json.load(target)
        changes.extend(data)
changes = [x for x in changes if x["consequent"] != [""]]


def clone_target_repo(owner, repo):
    data_repo_dir = "data/repos"
    if not os.path.exists(data_repo_dir + "/" + repo):
        if not os.path.exists(data_repo_dir):
            os.makedirs(data_repo_dir)
        print("Cloning " + data_repo_dir + "/" + repo)
        if "github_token" in config:
            git_url = "https://" + config["github_token"] + ":@github.com/" + owner + "/" + repo + ".git"
        else:
            git_url = "https://github.com/" + owner + "/" + repo + ".git"
        git.Git(data_repo_dir).clone(git_url)
    else:
        pass


def list_paths(root_tree, path=Path(".")):
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)


def get_all_file_contents(repo):
    target_repo = git.Repo("data/repos/" + repo)
    paths = [str(x) for x in list_paths(target_repo.commit("HEAD").tree)
             if any([str(x).endswith(y) for y in lang_extentions[lang]]) and
                (not ignore_test or "test" in str(x))]
    contents = {}
    for x in paths:
        with open("{}/data/repos/{}/{}".format(os.getcwd(), repo, x), "r", encoding='utf-8') as target:
            contents["{}/{}".format(repo, x)] = target.read()
    # return {f"{repo}\\{x}": target_repo.git.show('HEAD:{}'.format(x)) for x in paths}
    return contents

def make_matched_files(contents, re_condition, re_consequent):
    consequent_files = {path for path, content in contents.items() if re_consequent.search(content)}
    if not consequent_files:
        return ({}, {})
    condition_files = {path for path, content in contents.items() if re_condition.search(content)}

    # origin_condition = condition_files.difference(consequent_files)
    return (condition_files, consequent_files.difference(condition_files))


all_contents = {}

print("Collecting file contents...")
for project in projects:
    print(project)
    clone_target_repo(project["owner"], project["repo"])
    file_contents = get_all_file_contents(project["repo"])
    all_contents.update(file_contents)
print("Success Collecting %d files!" % len(all_contents))

print("Checking Rules...")

duplicates_sha = []

all_changes = []

changes_size = len(changes)

for i, change in enumerate(changes):
    if (change["condition"], change["consequent"]) in duplicates_sha:
        continue

    re_condition = snippet2RegexCondition(change["condition"])
    re_consequent = snippet2RegexCondition(change["consequent"])
    if re_condition is None or re_consequent is None:
        continue
    sys.stdout.write("\r%d / %d changes, %d rules are collected" % (i, changes_size, len(all_changes)))

    origin_condition, origin_consequent = make_matched_files(all_contents, re_condition, re_consequent)
    consequent_len = len(origin_consequent)
    if consequent_len == 0 or len(origin_condition) == 0:
        continue

    change["popularity"] = consequent_len / len(origin_condition.union(origin_consequent))
    
    if change["popularity"] > 0.1:
        change["applicable_files"] = list(origin_condition) if len(origin_condition) < 10 else list(origin_condition)[:9]
        change["links"] = ["https://github.com/%s/commit/%s" % (change["repository"], change["sha"])]
        duplicates_sha.append((change["condition"], change["consequent"]))
        all_changes.append(change)


validate_by = "pulls" if "pull" in config["validate_by"] else "master"

if validate_by != learn_from:
    changes = []
    change_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang + "_" + validate_by + "2.json"
                    for x in projects]
    for change_file in change_files:
        print("Combine from " + change_file)
        with open(change_file, "r") as target:
            data = json.load(target)
            changes.extend(data)

# contents = "number" if "pulls" == validate_by else "sha"
# contents_type = "pull" if "pulls" == validate_by else "commit"
# successed_numbers = []
# changes_size = len(all_changes)
# output = []

# for i, change in enumerate(all_changes):
#     if "/".join([change["repository"], contents_type, str(change[contents])]) in successed_numbers:
#         continue
#     sys.stdout.write("\r%d / %d rules are collected" %
#                     (i + 1, changes_size))
#     tmp_change = change

#     re_condition = snippet2RegexCondition(change["condition"])
#     re_consequent = snippet2RegexCondition(change["consequent"])

#     date = dt.strptime(change["created_at"],"%Y-%m-%d %H:%M:%S")
#     condition_change = [x for x in changes
#                         if re_condition.search("\n".join(x["condition"]))
#                         and dt.strptime(x["created_at"],"%Y-%m-%d %H:%M:%S") > date]

#     if len(condition_change) == 0:
#         output.append(tmp_change)
#         continue
#     consequent_change = ["/".join([x["repository"], contents_type, str(x[contents])]) for x in condition_change if re_consequent.search("\n".join(x["consequent"]))]

#     successed_number = list({x for x in consequent_change if x not in successed_numbers})
#     tmp_change["exception_links"] = list({"https://github.com/%s/%s/%s" % (x["repository"], contents_type, str(x[contents])) for x in condition_change
#                                             if "/".join([x["repository"], contents_type, str(x[contents])]) not in successed_number})

#     successed_numbers.extend(successed_number)
#     tmp_change["links"].extend(["https://github.com/%s" % x for x in successed_number])
#     tmp_change["frequency"] = len(successed_number)
#     tmp_change["accuracy"] = tmp_change["frequency"] / (tmp_change["frequency"] + len(tmp_change["exception_links"]))
#     output.append(tmp_change)

if len(projects) == 1:
    OUT_TOKEN_NAME = "data/changes/" + projects[0]["owner"] + "_" + projects[0]["repo"] + \
    "_" + lang + "_" + learn_from + "_devreplay2.json"
else:
    OUT_TOKEN_NAME = "data/changes/devreplay.json"

output = sorted(all_changes, key=lambda x: x["popularity"], reverse=True)
with open(OUT_TOKEN_NAME, "w") as target:
    print("Success to validate the changes Output is " + OUT_TOKEN_NAME)
    json.dump(output, target, indent=2)
