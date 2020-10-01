import csv
import json
from typing import Any, Dict, List

def combinePatterns(parameter_list):
    """
    類似した変更を削除する
    """
    return []

def readsstubs() -> List[Dict[str, Any]]:
    with open('data/sstubs/sstubs.json', 'r') as sstubs_file:
        reader = json.load(sstubs_file)
        return reader

def main():
    # sstubs形式にプロジェクトの変更履歴を収集する
    bugs = readsstubs()
    print(bugs[:1])
    for bug in bugs[:1]:
        for key, value in bug.items():
            print(key)
            print(value)
    # 一箇所のみの修正だけを対象とする

    # 空白などはもちろん削除

    # CommitIdからコミットメッセージを取得する

    # パターンのメッセージをコミットメッセージにする

    return


if __name__ == "__main__":
    main()
