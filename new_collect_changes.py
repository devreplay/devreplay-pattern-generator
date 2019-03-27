"""
Combined collect_pulls.py and collect_changes.py
Get data at once
Usage: python3 collect_pulls.py
"""
import sys
from csv import DictReader
from json import dump
from time import sleep
from configparser import ConfigParser
from unidiff import PatchSet, errors
from urllib.request import urlopen
from github import Github
from CodeTokenizer.tokenizer import TokeNizer
from lang_extentions import lang_extentions

config = ConfigParser()
config.read('config')
user = config["GitHub"]["id"]
password = config["GitHub"]["password"]
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]

TN = TokeNizer(lang)
g = Github(user, password)


def curl_diffs(diff_url):
    changes_sets = []
    try:
        url_diff = urlopen(diff_url)
        diffs = PatchSet(url_diff, encoding="utf-8")
    except (UnicodeDecodeError, errors.UnidiffParseError):
        print("UnicodeDecodeError:" + diff_url)
        return []

    filtered_diffs = [x for x in diffs
                      if x.is_modified_file
                      and any([x.path.endswith(y) for y in lang_extentions[lang]])]
    for diff in filtered_diffs:
        for hunk in diff:
            source = "".join([x.value for x in hunk if x.is_removed])
            target = "".join([x.value for x in hunk if x.is_added])
            if source == target:
                continue
            changes_set = TN.make_change_set(source, target)
            if changes_set == -1:
                continue

            changes_sets.append(
                {"changes_set": changes_set,
                 "file_path": diff.path})
    return changes_sets


def get_pulls(owner, repo_name):
    results = []
    print(owner + "/" + repo_name)
    repo = g.get_repo(owner + "/" + repo_name)
    pulls = repo.get_pulls(state='close', sort='created', base='master')

    for x in pulls:
        if not x.merged:
            continue
        ratelimit = g.get_rate_limit().core.remaining
        if ratelimit < 100:
            print("Sleeping for replenish rate limit")
            sleep(3600)
            ratelimit = g.get_rate_limit().core.remaining
        commits = x.get_commits()
        commits_len = len(list(commits))
        if commits_len == 1:
            continue
        first_commit_sha = commits[0].sha
        last_commit_sha = commits[-1].sha

        one_n_diff_url = repo.compare(
            first_commit_sha, last_commit_sha).diff_url
        sys.stdout.write("\r%s pulls" % (x.number))
        result = {
            "number": x.number,
            "commit_len": commits_len,
            "created_at": x.created_at,
            "merged_at": x.merged_at,
            "merged_by": x.merged_by.login,
            "1-n_url": one_n_diff_url
        }
        changes_sets = curl_diffs(one_n_diff_url)
        if changes_set == []:
            continue
        for changes_set in changes_sets:
            result["changes_set"] = changes_set["changes_set"]
            result["file_path"] = changes_set["file_path"]

            results.append(result)
    return results


def main():
    results = get_pulls(owner, repo)
    out_name = "data/changes/" + owner + "_" + repo + "_" + lang + "3.json"

    with open(out_name, "w", encoding='utf-8') as f:
        dump(results, f, indent=1)


if __name__ == '__main__':
    main()
