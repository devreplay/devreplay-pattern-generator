import sys
import os
import re
import json
import csv
from collections import defaultdict, OrderedDict
from configparser import ConfigParser
from pathlib import Path

import git

from lang_extentions import lang_extentions
from CodeTokenizer.tokenizer import TokeNizer

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]
TN = TokeNizer(lang)


CHANGE_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + ".json"
OUT_TOKEN_NAME = "data/tokens/" + owner + "_" + repo + "_" + lang + "_latest.json"


def list_paths(root_tree, path=Path(".")):
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)

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

def getChangesTokens(changes_set):
    tokens = {"A": [], "B": []}
    for change in changes_set:
        before = [x for x in change[2:].split("-->")[0][:-1].split(" ")
                    if any([y.isalnum() for y in x])]
        after = [x for x in change[2:].split("-->")[1][1:].split(" ")
                    if any([y.isalnum() for y in x])]

        tokens["A"].extend(before)
        tokens["B"].extend(after)
    return tokens

def searchTokenCharcter(target_repo, sha, files = [], condition_tokens = []):
    tokens = defaultdict(list)
    for path in files:
        file_contents = target_repo.git.show('{}:{}'.format(sha, path))
        for token in [x for x in condition_tokens if x in file_contents]:
            tokens[token].append(path)

    return tokens

# 対象プロジェクトをクローン or 特定

# clone_target_repo()
target_repo = git.Repo("data/repos/" + repo)

with open(CHANGE_JSON_NAME, "r") as json_file:
    changes = json.load(json_file)

url_re = re.compile(r"https://github\.com/" + owner + r"/" + repo + r"/compare/(\w+)\.\.\.(\w+)\.diff")

output = []
changes_len = len(changes)
for i, change in enumerate(changes):
    sys.stdout.write("\r%d / %d pulls" %
                    (i + 1, changes_len))
    token_dict = defaultdict()

    match = url_re.fullmatch(change["1-n_url"])
    if match is None:
        continue
    token_dict["number"] = change["number"]
    token_dict["sha"] = match.group(2)
    token_dict["changes_set"] = [x for x in change["changes_set"]
                                 if x.startswith("*")]
    changes_tokens = getChangesTokens(token_dict["changes_set"])
    if changes_tokens["A"] + changes_tokens["B"] == []:
        continue

    changed_diff_index = target_repo.commit(token_dict["sha"]).diff(target_repo.commit("HEAD"))

    deleted_file = [x.a_rawpath.decode('utf-8') for x in changed_diff_index.iter_change_type("D")]
    changed_file = [x.a_rawpath.decode('utf-8') for x in changed_diff_index.iter_change_type("M")]
    
    deleted_file = [x for x in deleted_file + changed_file
                    if any([str(x).endswith(y) for y in lang_extentions[lang]])]

    token_dict["original_tokens"] = searchTokenCharcter(target_repo, token_dict["sha"], deleted_file, set(changes_tokens["A"] + changes_tokens["B"]))

    output.append(token_dict)

with open(OUT_TOKEN_NAME + ".json", "w") as target:
    json.dump(output, target, indent=2)
