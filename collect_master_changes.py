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
from datetime import datetime

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
    changes_sets = make_master_diff(target_repo, lang)

    out_name = "data/changes/" + owner + "_" + repo + "_" + lang + "ss.json"

    with open(out_name, "w", encoding='utf-8') as f:
        dump(changes_sets, f, indent=1)


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

def make_master_diff(target_repo, lang):
    change_sets = []

    commits = list(target_repo.iter_commits("master"))
    for i, commit in enumerate(commits):
        if commit.message.startswith("Merge"):
            continue

        sys.stdout.write("\r%d/%d commits %d / %d changes" % (i, len(commits), len(change_sets), change_size))
        author = commit.author.name
        sha = commit.hexsha
        created_at = str(datetime.fromtimestamp(commit.authored_date))

        diff_index = commit.diff(sha + "~1")
        for diff_item in [x for x in diff_index.iter_change_type('M')
                          if any([x.a_rawpath.decode('utf-8').endswith(y)
                                 for y in lang_extentions[lang]])]:
            source = diff_item.a_blob.data_stream.read().decode('utf-8')
            target = diff_item.b_blob.data_stream.read().decode('utf-8')
            if source == target:
                continue
            hunks = make_hunks(source.splitlines(keepends=True), target.splitlines(keepends=True))

            for hunk in hunks:
                # try:
                #     diff_result = TN.get_abstract_tree_diff(hunk["source"], hunk["target"])
                # except:
                #     continue
                # if not is_valued_change(diff_result):
                #     continue
                # hunk["source"] = tokens2Realcode(diff_result["condition"])
                # hunk["target"] = tokens2Realcode(diff_result["consequent"])

                out_metricses = {
                    "sha": sha,
                    "author":author,
                    "created_at": created_at,
                    "file_path": diff_item.a_rawpath.decode('utf-8'),
                    "condition": hunk["source"].splitlines(),
                    "consequent": hunk["target"].splitlines()
                }
                if out_metricses["condition"] != []:
                    change_sets.append(out_metricses)
        
        if i > change_size:
            break
        
    return change_sets

if __name__ == '__main__':
    main()
