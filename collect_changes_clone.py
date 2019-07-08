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
from urllib.request import urlopen, Request
from configparser import ConfigParser
from CodeTokenizer.tokenizer import TokeNizer
from lang_extentions import lang_extentions
import git

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]
TN = TokeNizer(lang)
DIVIDE_PER = 100

def main():
    """
    The main
    """
    clone_target_repo()
    target_repo = git.Repo("data/repos/" + repo)
    changes_sets = get_project_changes(owner, repo, lang, target_repo)

    out_name = "data/changes/" + owner + "_" + repo + "_" + lang + "_last.json"

    with open(out_name, "w", encoding='utf-8') as f:
        dump(changes_sets, f, indent=1)


def get_project_changes(owner, repo, lang, target_repo, diffs_file=None):
    changes_sets = []
    if diffs_file is None:
        diffs_file = "data/pulls/" + owner + "_" + repo + ".csv"
    with open(diffs_file, "r", encoding="utf-8") as diffs:
        reader = DictReader(diffs)
        for i, diff_path in enumerate(reader):
            if diff_path["commit_len"] == "1":
                continue
            sys.stdout.write("\r%s pulls" % (diff_path["number"]))

            changes_set = make_pull_diff(target_repo, diff_path)
            if changes_set == []:
                continue
            changes_sets.extend(changes_set)
            if (len(changes_sets) + 1) % DIVIDE_PER == 0:
                out_name = "data/changes/" + owner + "_" + repo + "_" + lang + "_" + str(i) + ".json"

                with open(out_name, "w", encoding='utf-8') as f:
                    dump(changes_sets, f, indent=1)
                changes_sets = []

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

def make_pull_diff(target_repo, diff_path):
    change_sets = []
    try :
        original_commit = target_repo.commit(diff_path["first_commit_sha"])
        changed_commit = target_repo.commit(diff_path["merge_commit_sha"])
    except:
        return []
    diff_index = original_commit.diff(changed_commit)
    if original_commit.message.startswith("Merge") or changed_commit.message.startswith("Merge"):
        return []
    for diff_item in diff_index.iter_change_type('M'):
        if not any([diff_item.a_rawpath.decode('utf-8').endswith(x) 
                    for x in lang_extentions[lang]]):
            continue
        source = diff_item.a_blob.data_stream.read().decode('utf-8')
        target = diff_item.b_blob.data_stream.read().decode('utf-8')

        out_metricses = {
            "number": int(diff_path["number"]),
            "commit_len": int(diff_path["commit_len"]),
            "created_at": diff_path["created_at"],
            "merged_at": diff_path["merged_at"],
            "merged_by": diff_path["merged_by"],
            "1-n_url": diff_path["1-n_url"],
            "file_path": diff_item.a_rawpath.decode('utf-8'),
            "changes_set": TN.make_change_set2(source, target)
        }
        if out_metricses["changes_set"] == -1:
            continue
        change_sets.append(out_metricses)
        
    return change_sets

if __name__ == '__main__':
    main()
