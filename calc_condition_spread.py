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

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]


CHANGE_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + ".json"
OUT_TOKEN_NAME = "data/tokens/" + owner + "_" + repo + "_" + lang + "_HEAD.json"
OUT_TOKEN_NAME2 = "data/tokens/" + owner + "_" + repo + "_" + lang + "_ORIGINAL.json"


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

def searchTokenCharcter(sha, files = [], condition_tokens = []):
    new_files = []
    for path in files:
        file_contents = target_repo.git.show('{}:{}'.format(sha, path))
        if all([x in file_contents for x in condition_tokens]):
            new_files.append(path)

    return new_files

def list_paths(root_tree, path=Path(".")):
    for blob in root_tree.blobs:
        yield path / blob.name
    for tree in root_tree.trees:
        yield from list_paths(tree, path / tree.name)

def get_all_tokens(tokens):
    paths = [str(x) for x in list_paths(target_repo.commit("HEAD").tree)
             if any([str(x).endswith(y) for y in lang_extentions[lang]])]
    contained_tokens = defaultdict(list)
    for path in paths:
        file_contents = target_repo.git.show('HEAD:{}'.format(path))
        for token in [x for x in tokens if x in file_contents]:
            contained_tokens[token].append(path)
    return contained_tokens

def make_file_index():
    if os.path.exists(OUT_TOKEN_NAME):
        print("already exist")
        with open(OUT_TOKEN_NAME, "r") as target:
            changes = json.load(target)
        return changes
    # 対象とするトークンを決定
    target_tokens = [x["identifiers"]["condition"] + x["identifiers"]["consequent"] for x in changes]
    target_tokens = list(set(itertools.chain.from_iterable(target_tokens)))
    latest_tokens = get_all_tokens(target_tokens)
    with open(OUT_TOKEN_NAME, "w") as target:
        json.dump(latest_tokens, target, indent=2)
    return latest_tokens

clone_target_repo()
target_repo = git.Repo("data/repos/" + repo)

with open(CHANGE_JSON_NAME, "r") as json_file:
    changes = json.load(json_file)

latest_tokens = make_file_index()

output = []
changes_len = len(changes)
head_commit = target_repo.commit("HEAD")

for i, change in enumerate(reversed(changes)):
    sys.stdout.write("\r%d / %d pulls %d changes are collected" %
                    (i + 1, changes_len, len(output)))
    token_dict = change

    ident_condition = change["identifiers"]["condition"]
    ident_consequent = change["identifiers"]["consequent"]
    target_tokens = list(set(ident_condition + ident_consequent))
    if target_tokens == []:
        continue

    changed_diff_index = target_repo.commit(change["sha"]).diff(head_commit)

    # added_file = [x.a_rawpath.decode('utf-8') for x in changed_diff_index.iter_change_type("A")]
    # deleted_file = [x.a_rawpath.decode('utf-8') for x in changed_diff_index.iter_change_type("D")]
    changed_file = [str(x.a_rawpath.decode('utf-8')) for x in changed_diff_index.iter_change_type("M")
                    if any([str(x.a_rawpath.decode('utf-8')).endswith(y) for y in lang_extentions[lang]])]
    
    # deleted_file = [x for x in deleted_file + changed_file
    #                 if any([str(x).endswith(y) for y in lang_extentions[lang]])]
    # added_file = [x for x in added_file + changed_file
    #                 if any([str(x).endswith(y) for y in lang_extentions[lang]])]

    condition_files = searchTokenCharcter(change["sha"], changed_file, ident_condition)
    token_dict["# condition_files"] = len(condition_files)
    
    head_condition = [list(set(latest_tokens[x]) & set(changed_file))
                      for x in ident_condition if x in latest_tokens]
    if len(head_condition) == 0:
        token_dict["# condition_files_HEAD"] = 0
    elif len(head_condition) == 1:
        token_dict["# condition_files_HEAD"] = len(head_condition[0])
    else:
        token_dict["# condition_files_HEAD"] = len([x for x in head_condition[0]
                                                    if all([x in y for y in head_condition[1:]])])

    if ident_condition == ident_consequent:
        token_dict["consequent_files"] = token_dict["# condition_files"]
        token_dict["consequent_files_HEAD"] = token_dict["# condition_files_HEAD"]
    else:
        token_dict["# consequent_files"] = len(searchTokenCharcter(change["sha"], changed_file, ident_consequent))
        head_consequent = [list(set(latest_tokens[x]) & set(changed_file))
                           for x in ident_consequent if x in latest_tokens]        
        if len(head_consequent) == 0:
            token_dict["# consequent_files_HEAD"] = 0
        elif len(head_consequent) == 1:
            token_dict["# consequent_files_HEAD"] = len(head_consequent[0])
        else:
            token_dict["# consequent_files_HEAD"] = len([x for x in head_consequent[0]
                                                    if all([x in y for y in head_consequent[1:]])])  
    token_dict["# changed_files"] = len(changed_file)

    output.append(token_dict)

print()
with open(OUT_TOKEN_NAME2, "w") as target:
    json.dump(output, target, indent=2)
