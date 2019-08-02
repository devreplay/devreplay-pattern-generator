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
    if condition_tokens == []:
        return []
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

def make_file_index(changes):
    if os.path.exists(OUT_TOKEN_NAME):
        with open(OUT_TOKEN_NAME, "r") as target:
            changes = json.load(target)
        return changes
    target_tokens = [x["identifiers"]["condition"] + x["identifiers"]["consequent"] for x in changes]
    target_tokens = list(set(itertools.chain.from_iterable(target_tokens)))
    latest_tokens = get_all_tokens(target_tokens)
    with open(OUT_TOKEN_NAME, "w") as target:
        json.dump(latest_tokens, target, indent=2)
    return latest_tokens

def make_repeated_rules(rules):
    correct_rules = []
    for rule in rules:
        condition = rule["identifiers"]["condition"]
        consequent = rule["identifiers"]["consequent"]
        condition_changes = list(set(
                            [x["number"] for x in changes 
                             if x["number"] > rule["number"] and\
                             all([y in x["identifiers"]["condition"] for y in condition]) and\
                             all([y in x["identifiers"]["consequent"] for y in consequent])]))

        condition_changes_num = len(condition_changes)
        rule["frequency"] = condition_changes_num
        rule["repeated_pr_id"] = condition_changes
        correct_rules.append(rule)
    return sorted(correct_rules, key=lambda x: x["frequency"], reverse=True)

def make_token_ratio(ident_condition, ident_consequent, changed_file, condition_head, consequent_head):
    token_dict = {}
    if set(ident_condition).issubset(set(ident_consequent)):
        consequent_files = searchTokenCharcter(change["sha"], changed_file, ident_consequent)
        token_dict["#consequent_files"] = len(consequent_files)
        token_dict["#condition_files"] = len(searchTokenCharcter(change["sha"],
                                                                 consequent_files, ident_consequent))
    elif set(ident_consequent).issubset(set(ident_condition)):
        condition_files = searchTokenCharcter(change["sha"], changed_file, ident_condition)        
        token_dict["#condition_files"] = len(condition_files)
        token_dict["#consequent_files"] = len(searchTokenCharcter(change["sha"],
                                                                  condition_files, ident_consequent))
    else:
        token_dict["#condition_files"] = len(searchTokenCharcter(change["sha"],
                                                                 changed_file, ident_condition))
        token_dict["#consequent_files"] = len(searchTokenCharcter(change["sha"],
                                                                  changed_file, ident_consequent))
    
    token_dict["condition_ratio"] = (condition_head + 1) / (token_dict["#condition_files"] + 1)
    token_dict["consequent_ratio"] = (consequent_head + 1) / (token_dict["#consequent_files"] + 1)

    token_dict["#changed_files"] = len(changed_file)
    return token_dict

clone_target_repo()
target_repo = git.Repo("data/repos/" + repo)

with open(CHANGE_JSON_NAME, "r") as json_file:
    changes = json.load(json_file)

latest_tokens = make_file_index(changes)

output = []
changes_len = len(changes)
head_commit = target_repo.commit("HEAD")

for i, change in enumerate(reversed(changes)):
    sys.stdout.write("\r%d / %d pulls %d rules are collected" %
                    (i + 1, changes_len, len(output)))
    token_dict = change

    ident_condition = change["identifiers"]["condition"]
    ident_consequent = change["identifiers"]["consequent"]
    if ident_condition == ident_consequent or list(set(ident_condition + ident_consequent)) == []:
        continue

    consequent_in_condition = set(ident_consequent).issubset(set(ident_condition)) or\
                              all([any([x in y for y in ident_condition]) for x in ident_consequent])
    condition_in_consequent = set(ident_condition).issubset(set(ident_consequent)) or\
                              all([any([x in y for y in ident_consequent]) for x in ident_condition])  

    changed_diff_index = target_repo.commit(change["sha"]).diff(head_commit)

    added_file = [x.a_rawpath.decode('utf-8') for x in changed_diff_index.iter_change_type("A")]
    changed_file = [x.a_rawpath.decode('utf-8') for x in changed_diff_index.iter_change_type("M")]
    changed_file = [str(x) for x in changed_file + added_file
                    if any([str(x).endswith(y) for y in lang_extentions[lang]])]

    if any([x not in latest_tokens for x in ident_condition]) or\
       any([x not in latest_tokens for x in ident_consequent]):
        continue

    head_condition = [list(set(latest_tokens[x]) & set(changed_file))
                      for x in ident_condition]

    head_consequent = [list(set(latest_tokens[x]) & set(changed_file))
                       for x in ident_consequent]        
    if len(head_consequent) == 0:
        continue
    elif len(head_consequent) == 1:
        adopted_files = head_consequent[0]
    else:
        adopted_files = [x for x in head_consequent[0]
                                                if all([x in y for y in head_consequent[1:]])]

    if len(head_condition) == 0:
        continue
    elif len(head_condition) == 1:
        token_dict["adoptable_files"] = head_condition[0]
    else:
        token_dict["adoptable_files"] = [x for x in head_condition[0]
                                         if all([x in y for y in head_condition])]

    if consequent_in_condition:
        adopted_files = [x for x in adopted_files if x not in token_dict["adoptable_files"]]
    elif condition_in_consequent:
        token_dict["adoptable_files"] = [x for x in token_dict["adoptable_files"] if x not in adopted_files]
    else:
        tmp = token_dict["adoptable_files"]
        token_dict["adoptable_files"] = [x for x in token_dict["adoptable_files"]\
                                         if x not in adopted_files]
        abopted_files = [x for x in adopted_files if x not in tmp]



    token_dict["#condition_files"] = len(token_dict["adoptable_files"])
    token_dict["#consequent_files"] = len(adopted_files)

    # original_stat = make_token_ratio(ident_condition, ident_consequent, changed_file,
    #                                  token_dict["#condition_files"], token_dict["#consequent_files"]) 
    # token_dict.update(original_stat)
    # if not (token_dict["consequent_ratio"] > 1.0 or token_dict["condition_ratio"] < 1.0) or\
    #     token_dict["consequent_ratio"] < token_dict["condition_ratio"]:
    #     continue
    if token_dict["#condition_files"] == 0:
        if token_dict["#consequent_files"] != 0:
            token_dict["consequent/condition"] = token_dict["#consequent_files"]
        else:
            continue
    else:
        token_dict["consequent/condition"] = token_dict["#consequent_files"] /\
                                         token_dict["#condition_files"]

    

    if token_dict["consequent/condition"] > 1.0 or\
    (len(ident_condition) == 1 and len(ident_consequent) == 1 and token_dict["consequent/condition"] > 0.5):
        output.append(token_dict)

output = make_repeated_rules(output)
output = sorted(output, key=lambda x: x["consequent/condition"], reverse=True)

print("output %d rules" % len(output))
with open(OUT_TOKEN_NAME2, "w") as target:
    json.dump(output, target, indent=2)
