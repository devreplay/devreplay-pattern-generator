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
from json import dump, loads, dumps, load
from unidiff import PatchSet, errors
import difflib
from configparser import ConfigParser
from CodeTokenizer.tokenizer import TokeNizer
from lang_extentions import lang_extentions
import git
from datetime import datetime
from collector.pulls_collector import PullsCollector

with open("config.json", "r") as json_file:
    config = load(json_file)

token = config["github_token"]
lang = config["lang"]
TN = TokeNizer(lang)
change_size = config["change_size"]
all_author = config["all_author"] if "all_author" in config else True
authors = config["authors"] if "authors" in config else []

def main():
    """
    The main
    """

    projects = config["projects"]
    learn_from_pulls = "pull" in config["learn_from"]
    validate_by_pulls = "pull" in config["validate_by"]
    for projet in projects:
        owner = projet["owner"]
        repo = projet["repo"]

        clone_target_repo(owner, repo)
        target_repo = git.Repo("data/repos/" + repo)
        print(f"{owner}/{repo} ")

        # Learn or validate from master pull request
        if learn_from_pulls or validate_by_pulls:            
            collect_target_pulls(owner, repo, token)

            abstracted = learn_from_pulls
            print("collecting the pull changes...")
            changes_sets = make_pull_diff(target_repo, owner, repo, abstracted)

            out_name = "data/changes/" + owner + "_" + repo + "_" + lang + "_pulls.json"
            with open(out_name, "w", encoding='utf-8') as f:
                print("\nSuccess to collect the pull changes Output is " + out_name)
                dump(changes_sets, f, indent=1)

        # Learn or validate from master branch
        if not (learn_from_pulls and validate_by_pulls):
            abstracted = not learn_from_pulls
            print("collecting the master changes...")
            changes_sets = make_master_diff(target_repo, owner, repo, abstracted)

            out_name = "data/changes/" + owner + "_" + repo + "_" + lang + "_master.json"
            with open(out_name, "w", encoding='utf-8') as f:
                print("\nSuccess to collect the master changes Output is " + out_name)
                dump(changes_sets, f, indent=1)



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

def collect_target_pulls(owner, repo, token):
    file_name = f'data/pulls/{owner}_{repo}.csv'
    if not os.path.exists(file_name):
        print(f"collecting {owner}/{repo} pulls...")
        collector = PullsCollector(token, owner, repo)
        collector.save_all(file_name)
        print(f"Succeeded collecting {owner}/{repo} pulls!")
    else:
        pass
    # with open(file_name, "r", encoding="utf-8") as diffs:
    #     return list(DictReader(diffs))

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
                "condition": code_trip("".join(deleted_lines)),
                "consequent": code_trip("".join(added_lines)),
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
            "condition": code_trip("".join(deleted_lines)),
            "consequent": code_trip("".join(added_lines)),
        })
    return hunks

def code_trip(code):
    splited_code = code.splitlines(keepends=True)
    min_space = min(len(x) - len(x.lstrip()) for x in splited_code)
    return "".join([x[min_space:] for x in splited_code])

def is_defined_author(author):
    return all_author or\
       len(authors) == 0 or\
       any(author in x["git"] or author in x["github"] for x in authors)

def make_master_diff(target_repo, owner, repo, abstracted):
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
        try:
            diff_index = commit.diff(sha + "~1")
        except:
            continue

        created_at = str(datetime.fromtimestamp(commit.authored_date))
        hunks = make_abstracted_hunks(diff_index, abstracted)
        out_metricses = [{
            "repository": f"{owner}/{repo}",
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

def make_pull_diff(target_repo, owner, repo, abstracted):
    change_sets = []
    diffs_file = "data/pulls/" + owner + "_" + repo + ".csv"
    with open(diffs_file, "r", encoding="utf-8") as diffs:
        reader = sorted(list(DictReader(diffs)), key=lambda x: x["number"])
    for i, diff_path in enumerate(reversed(reader)):
        if diff_path["commit_len"] == "1" or not is_defined_author(diff_path["author"]):
            continue        
        try :
            original_commit = target_repo.commit(diff_path["first_commit_sha"])
            changed_commit = target_repo.commit(diff_path["merge_commit_sha"])
        except:
            continue
        commits = target_repo.iter_commits(diff_path["first_commit_sha"] + ".." + diff_path["merge_commit_sha"])
        if any([x.message.startswith("Merge") for x in commits]):
            continue

        sys.stdout.write("\r%d pulls id: %s, %d / %d changes" % 
                    (i, diff_path["number"], len(change_sets), change_size))

        diff_index = original_commit.diff(changed_commit)

        hunks = make_abstracted_hunks(diff_index, abstracted)
        out_metricses = [{
            "repository": f"{owner}/{repo}",
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
