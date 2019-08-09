"""
Get Style missing from diff file
Style misses list
* Rename identifier
* Large to Small (ex:"Style" to "style")
* only make new line
* Space or Tab
* Don't changed AST
"""
import sys
import os
from csv import DictReader
from json import dump
from unidiff import PatchSet, errors
import difflib
import io
from configparser import ConfigParser
from CodeTokenizer.tokenizer import TokeNizer, tokens2Realcode
from lang_extentions import lang_extentions
import git

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]
change_size = int(config["Target"]["change_size"])
TN = TokeNizer(lang)
DIVIDE_PER = 100

def main():
    """
    The main
    """
    clone_target_repo()
    target_repo = git.Repo("data/repos/" + repo)
    changes_sets = get_project_changes(owner, repo, lang, target_repo)

    out_name = "data/changes/" + owner + "_" + repo + "_" + lang + ".json"

    with open(out_name, "w", encoding='utf-8') as f:
        dump(changes_sets, f, indent=1)


def get_project_changes(owner, repo, lang, target_repo, diffs_file=None):
    changes_sets = []
    if diffs_file is None:
        diffs_file = "data/pulls/" + owner + "_" + repo + ".csv"
    with open(diffs_file, "r", encoding="utf-8") as diffs:
        reader = DictReader(diffs)
        for diff_path in reader:
            if diff_path["commit_len"] == "1":
                continue
            sys.stdout.write("\r%s pulls %d / %d changes" % (diff_path["number"], len(changes_sets), change_size))

            changes_set = make_pull_diff(target_repo, diff_path)
            if changes_set == []:
                continue
            changes_sets.extend(changes_set)
            if len(changes_sets) > change_size:
                return changes_sets

    return changes_sets


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

def make_hunks(source, target):
    hunks = []
    differ = difflib.ndiff(source, target)
    previous_symbol = " "
    deleted_lines = []
    added_lines = []
    for diff in differ:
        # print(diff)
        symbol = diff[0]
        if len(diff) < 3 or symbol == "?":
            continue
        line = diff[2:]

        if symbol not in ["+", previous_symbol] and deleted_lines != [] and added_lines != []:
            hunks.append({
                "source": "".join(deleted_lines),
                "target": "".join(added_lines),
            })
            deleted_lines = []
            added_lines = []

        if symbol == "-":
            deleted_lines.append(line)
        elif symbol == "+":
            added_lines.append(line)

        previous_symbol = symbol
    if deleted_lines != [] and added_lines != []:
        hunks.append({
            "source": "".join(deleted_lines),
            "target": "".join(added_lines),
        })
    return hunks

def is_valued_change(diff):
    return diff["identifiers"]["condition"] != diff["identifiers"]["consequent"]

def make_pull_diff(target_repo, diff_path):
    change_sets = []
    try :
        original_commit = target_repo.commit(diff_path["first_commit_sha"])
        changed_commit = target_repo.commit(diff_path["merge_commit_sha"])
    except:
        return []
    commits = target_repo.iter_commits(diff_path["first_commit_sha"] + ".." + diff_path["merge_commit_sha"])
    if  any([x.message.startswith("Merge") for x in commits]):
        return []
    diff_index = original_commit.diff(changed_commit)    
    for diff_item in diff_index.iter_change_type('M'):
        if not any([diff_item.a_rawpath.decode('utf-8').endswith(x) 
                    for x in lang_extentions[lang]]):
            continue
        source = diff_item.a_blob.data_stream.read().decode('utf-8')
        target = diff_item.b_blob.data_stream.read().decode('utf-8')
        if source == target:
            continue
        hunks = make_hunks(source.splitlines(keepends=True), target.splitlines(keepends=True))   

        for hunk in hunks:
            try:
                diff_result = TN.get_abstract_tree_diff(hunk["source"], hunk["target"])
            except:
                continue

            if not is_valued_change(diff_result):
                continue

            out_metricses = {
                "number": int(diff_path["number"]),
                "sha": diff_path["merge_commit_sha"],
                "author":diff_path["author"],
                "participant":diff_path["participant"],
                "created_at": diff_path["created_at"],
                "merged_at": diff_path["merged_at"],
                "merged_by": diff_path["merged_by"],
                "file_path": diff_item.a_rawpath.decode('utf-8'),
                "condition": tokens2Realcode(diff_result["condition"]).splitlines(),
                "consequent": tokens2Realcode(diff_result["consequent"]).splitlines()
            }
            if out_metricses["condition"] != []:
                change_sets.append(out_metricses)
        
    return change_sets

if __name__ == '__main__':
    main()
