# import csv
import json
from typing import Any, Dict, List, Counter
# import sys
# import os
# from csv import DictReader
from json import dump
# import difflib
from CodeTokenizer.tokenizer import TokeNizer
# from lang_extentions import lang_extentions
# import git
# from datetime import datetime, timedelta
# from collector.pulls_collector import PullsCollector

def combinePatterns(parameter_list):
    """
    類似した変更を削除する
    """
    return []

def readsstubs() -> List[Dict[str, Any]]:
    with open('data/sstubs/sstubs.json', 'r') as sstubs_file:
        reader = json.load(sstubs_file)
        return reader

def code_trip(splited_code, to_code=False):
    min_space = 0 if len(splited_code) == 0 else min(len(x) - len(x.lstrip()) for x in splited_code)
    splited_code = [x[min_space:].rstrip() for x in splited_code]
    if to_code:
        return splited_code
    return "\n".join(splited_code)

def makePattern():
    return []

def main():
    # sstubs形式にプロジェクトの変更履歴を収集する
    bugs = readsstubs()
    TN = TokeNizer("Java")
    hunks = []
    for bug in bugs:
        # bugType = bug["bugType"]
        # filePath = bug["bugFilePath"]
        project = bug["projectName"]
        bugType = bug["bugType"]
        before = bug['sourceBeforeFix']
        after = bug['sourceAfterFix']

        try:
            diff_result = TN.get_abstract_tree_diff(before, after)
        except Exception as e:
            print(e)
            continue
        diff_result["before"] = code_trip(diff_result["condition"].splitlines(), True)
        diff_result["after"] = code_trip(diff_result["consequent"].splitlines(), True)
            
        del diff_result['condition']
        del diff_result['consequent']
        del diff_result['abstracted']
        diff_result['author'] = project
        # TODO CommitIdからコミットメッセージを取得する
        # TODO パターンのメッセージをコミットメッセージにする
        diff_result['message'] = bugType

        hunks.append(diff_result)

    filtered_set = [x for x in hunks 
                    if x["before"] != x["after"] and x["before"] != []]
    unique_set = [(val["before"][0] + " *** " + val["after"][0], {'bugType': val['message'],'author': val['author']}) for val in filtered_set]
    count_set = Counter([x[0] for x in unique_set])
    out_hunks = [{
        "change": key.split(" *** "),
        "count": x,
        'bugType': list(set([x['bugType'] for i, x in unique_set if i == key])),
        'author': list(set([x['author'] for i, x in unique_set if i == key]))} for key, x in count_set.items()]

    out_hunks = sorted(out_hunks, key=lambda k: k['count']) 
    out_name = f"data/changes/sstubs_devreplay.json"
    with open(out_name, "w", encoding='utf-8') as f:
        print("\nSuccess to collect the pull changes Output is " + out_name)
        dump(out_hunks, f, indent=1)

    out_name = f"data/changes/sstubs_devreplay_all.json"
    with open(out_name, "w", encoding='utf-8') as f:
        print("\nSuccess to collect the pull changes Output is " + out_name)
        dump(hunks, f, indent=1)

    return

if __name__ == "__main__":
    main()
