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
from json import dump, loads, dumps
from unidiff import PatchSet, errors
import difflib
from configparser import ConfigParser
from CodeTokenizer.tokenizer import TokeNizer
from lang_extentions import lang_extentions
import git
from datetime import datetime

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]
TN = TokeNizer(lang)
change_size = int(config["Option"]["rule_size"])
learn_from_pulls = config["Option"].getboolean("learn_from_pulls")
abstracted = config["Option"].getboolean("abstract_master_change")
defined_author = config["Option"]["developer_github_id"] if learn_from_pulls and "developer_github_id" in config["Option"] else\
                 config["Option"]["developer_git_username"] if not learn_from_pulls and "developer_git_username" in config["Option"] else\
                     None

def main():
    """
    The main
    """
    clone_target_repo()
    target_repo = git.Repo("data/repos/" + repo)

    if learn_from_pulls:
        out_name = "data/changes/" + owner + "_" + repo + "_" + lang + "_pulls.json"
        changes_sets = get_project_changes(owner, repo, lang, target_repo)
        with open(out_name, "w", encoding='utf-8') as f:
            print("\nSuccess to collect the pull changes Output is " + out_name)
            dump(changes_sets, f, indent=1)

    out_name = "data/changes/" + owner + "_" + repo + "_" + lang + "_master.json"
    print("collecting the master changes...")
    changes_sets = make_master_diff(target_repo, lang)
    with open(out_name, "w", encoding='utf-8') as f:
        print("\nSuccess to collect the master changes Output is " + out_name)
        dump(changes_sets, f, indent=1)


def get_project_changes(owner, repo, lang, target_repo, diffs_file=None):
    changes_sets = []
    diffs_file = "data/pulls/" + owner + "_" + repo + ".csv"
    with open(diffs_file, "r", encoding="utf-8") as diffs:
        reader = DictReader(diffs)
        for i, diff_path in enumerate(reversed(list(reader))):
            if diff_path["commit_len"] == "1" or not is_defined_author(diff_path["author"]):
                continue
            sys.stdout.write("\r%d pulls id: %s, %d / %d changes" % 
                             (i, diff_path["number"], len(changes_sets), change_size))

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
        print("Cloning " + data_repo_dir + "/" + repo)
        if "Token" in config["GitHub"]:
            git_url = "https://" + config["GitHub"]["Token"] + ":@github.com/" + owner + "/" + repo +".git"
        else:
            git_url = "https://github.com/" + owner + "/" + repo +".git"
        git.Git(data_repo_dir).clone(git_url)

def make_abstracted_hunks(diff_index, is_abstract):
    out_hunks = []
    for diff_item in [x for x in diff_index.iter_change_type('M')
                     if any([x.a_rawpath.decode('utf-8').endswith(y)
                             for y in lang_extentions[lang]])]:
        source = diff_item.a_blob.data_stream.read().decode('utf-8')
        target = diff_item.b_blob.data_stream.read().decode('utf-8')
        if source == target:
            continue
        hunks = make_hunks(source.splitlines(keepends=True), target.splitlines(keepends=True))
        hunks = [x for x in hunks if x["condition"] != x["consequent"]]
        hunks = list(map(loads, set(map(dumps, hunks))))

        # file_path = diff_item.a_rawpath.decode('utf-8')
        if is_abstract:
            for hunk in hunks:
                try:
                    diff_result = TN.get_abstract_tree_diff(hunk["condition"], hunk["consequent"])
                except:
                    continue
                if diff_result["condition"] == diff_result["consequent"] or\
                    diff_result["condition"] == [] or\
                    diff_result["identifiers"]["condition"] == [] or\
                    diff_result["identifiers"]["consequent"] == []:
                    continue
 
                out_hunks.append({
                    "condition": diff_result["condition"].splitlines(),
                    "consequent": diff_result["consequent"].splitlines()
                })
        else:
            out_hunks.extend([{
                "condition": x["condition"].splitlines(),
                "consequent": x["consequent"].splitlines()
            } for x in hunks])
    
    out_hunks = list(map(loads, set(map(dumps, out_hunks))))
    return out_hunks

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
                "condition": "".join(deleted_lines).lstrip(),
                "consequent": "".join(added_lines).lstrip(),
            })
            deleted_lines = []
            added_lines = []

        if symbol == "-":
            deleted_lines.append(line)
        elif symbol == "+":
            added_lines.append(line)
        else:
            deleted_lines = []
            added_lines = []

        previous_symbol = symbol
    if deleted_lines != [] and added_lines != []:
        hunks.append({
            "condition": "".join(deleted_lines).lstrip(),
            "consequent": "".join(added_lines).lstrip(),
        })
    return hunks

def is_defined_author(author):
    return defined_author in [None, author]

def make_master_diff(target_repo, lang):
    change_sets = []

    commits = list(target_repo.iter_commits("master"))
    for i, commit in enumerate(commits):
        if commit.message.startswith("Merge"):
            continue

        sys.stdout.write("\r%d/%d commits %d / %d changes" % (i, len(commits), len(change_sets), change_size))
        author = commit.author.name
        if not is_defined_author(author):
            continue

        sha = commit.hexsha
        created_at = str(datetime.fromtimestamp(commit.authored_date))
        try:
            diff_index = commit.diff(sha + "~1")
        except:
            continue

        hunks = make_abstracted_hunks(diff_index, abstracted)

        out_metricses = [{
            "sha": sha,
            "author":author,
            "created_at": created_at,
            # "file_path": x["file_path"],
            "condition": x["condition"],
            "consequent": x["consequent"]
        } for x in hunks]
        change_sets.extend(out_metricses)
        
        if len(change_sets) > change_size:
            break
        
    return change_sets

def make_pull_diff(target_repo, diff_path):
    change_sets = []
    try :
        original_commit = target_repo.commit(diff_path["first_commit_sha"])
        changed_commit = target_repo.commit(diff_path["merge_commit_sha"])
    except:
        return []
    commits = target_repo.iter_commits(diff_path["first_commit_sha"] + ".." + diff_path["merge_commit_sha"])
    if any([x.message.startswith("Merge") for x in commits]):
        return []
    diff_index = original_commit.diff(changed_commit)

    hunks = make_abstracted_hunks(diff_index, True)
    out_metricses = [{
        "number": int(diff_path["number"]),
        "sha": diff_path["merge_commit_sha"],
        "author":diff_path["author"],
        "created_at": diff_path["created_at"],
        # "file_path": x["file_path"],
        "condition": x["condition"],
        "consequent": x["consequent"]
    } for x in hunks]
    change_sets.extend(out_metricses)
    
    if len(change_sets) > change_size:
        return change_sets

    return change_sets

if __name__ == '__main__':
    main()
