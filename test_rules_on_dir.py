import os
import git
import json
import re
import sys
from pathlib import Path
from lang_extentions import lang_extentions
from collections import defaultdict

with open("config.json", "r") as json_file:
    config = json.load(json_file)

lang = config["lang"]
projects = config["projects"]
validate_projects = config.get("validate_projects", [])

learn_from = "pulls" if "pull" in config["learn_from"] else "master"

group_changes = re.compile(r"\\\$\\{(\d+)(:[a-zA-Z_]+\\})")
simple_change = re.compile(r"[a-zA-Z_]+")

change_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + ".json"
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
        return r"(P=token" + str(tokenid + 1) + r"[a-zA-Z_]+)"
    else:
        identifier_ids.append(tokenid)
        return r"(?P<token" + str(tokenid + 1) + r">[a-zA-Z_]+)"

def snippet2Regex(snippet):
    identifier_ids = []
    joinedCondition = "\n".join(snippet)
    joinedCondition = re.escape(joinedCondition)
    joinedCondition = group_changes.sub(lambda m: group2increment(m, identifier_ids), joinedCondition)
    try:
        return re.compile(joinedCondition)
    except:
        return

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

def list_paths(root_tree, path=Path(".")):
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)

def get_all_file_contents(repo):
    target_repo = git.Repo("data/repos/" + repo)
    paths = [str(x) for x in list_paths(target_repo.commit("HEAD").tree)
             if any([str(x).endswith(y) for y in lang_extentions[lang]])]
    return [{"path": f"{repo}/{x}", "content": target_repo.git.show('HEAD:{}'.format(x))} for x in paths]

def make_matched_files(contents, re_condition, re_consequent):
    condition_files = [x["path"] for x in contents if re_condition.search(x["content"])]
    consequent_files = [x["path"] for x in contents if re_consequent.search(x["content"])]

    consequent_files = set(consequent_files)
    condition_files = set(condition_files)
    origin_condition = condition_files.difference(consequent_files)
    origin_consequent = consequent_files.difference(condition_files)
    return (origin_condition, origin_consequent)

all_changes = []
all_contents = []

print("Collecting file contents...")
for project in projects:
    print(project)
    clone_target_repo(project["owner"], project["repo"])
    file_contents = get_all_file_contents(project["repo"])
    all_contents.extend(file_contents)

all_validate_contents = []
if validate_projects != []:
    print("Collecting validate file contents...")
    for project in validate_projects:
        print(project)
        clone_target_repo(project["owner"], project["repo"])
        file_contents = get_all_file_contents(project["repo"])
        all_validate_contents.extend(file_contents)

print("Success Collecting %d files!" % len(all_contents))

print("Checking Rules...")

duplicates_sha = []

change_size = len(changes)
for i, change in enumerate(changes):
    if (change["condition"], change["consequent"]) in duplicates_sha:
        continue

    re_condition = snippet2Regex(change["condition"])
    re_consequent = snippet2Regex(change["consequent"])
    if re_condition == None or re_consequent == None:
        continue
    sys.stdout.write("\r%d / %d changes, %d rules collected" % (i, change_size, len(all_changes)))

    origin_condition, origin_consequent = make_matched_files(all_contents, re_condition, re_consequent)
    condition_len = len(origin_condition)
    consequent_len = len(origin_consequent)
    change["popularity"] = consequent_len / (consequent_len + condition_len) if consequent_len > 0 else 0

    if validate_projects != []:
        validate_condition, validate_consequent = make_matched_files(all_validate_contents, re_condition, re_consequent)
        validate_condition_len = len(validate_condition)
        validate_consequent_len = len(validate_consequent)
        change["self_popularity"] = validate_consequent_len / (validate_consequent_len + validate_condition_len) if validate_consequent_len > 0 else 0
        change["unchanged_files"] = list(validate_condition)
        total_conditon_len = validate_condition_len
    else:
        change["unchanged_files"] = list(origin_condition)
        total_conditon_len = condition_len
    
    if total_conditon_len != 0 and consequent_len != 0:
        change["link"] = "https://github.com/%s/commit/%s" % (change["repository"], change["sha"])
        duplicates_sha.append((change["condition"], change["consequent"]))
        all_changes.append(change)



print("Collecting validate file contents...")
for project in validate_projects:
    print(project)
    clone_target_repo(project["owner"], project["repo"])
    file_contents = get_all_file_contents(project["repo"])
    all_validate_contents.extend(file_contents)


if len(projects) == 1:
    OUT_TOKEN_NAME = "data/changes/" + projects[0]["owner"] + "_" + projects[0]["repo"] + \
    "_" + lang + "_" + learn_from + "_validated.json"
else:
    OUT_TOKEN_NAME = "data/changes/devreplay.json"

all_changes = sorted(all_changes, key=lambda x: x["popularity"], reverse=True)
with open(OUT_TOKEN_NAME, "w") as target:
    print("Success to validate the changes Output is " + OUT_TOKEN_NAME)
    json.dump(all_changes, target, indent=2)
