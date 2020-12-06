from json import load, dump
from os import replace
from subprocess import Popen, PIPE
from typing import Any, Dict, List
from csv import DictWriter
import sys

# from csv import DictWriter

# 生成したパターンによる精度と再現率をひょうか
# time series split cross-validationを用いる




def readsstubs() -> List[Dict[str, Any]]:
    with open('data/sstubs/sstubs.json', 'r') as sstubs_file:
        reader = load(sstubs_file)
        return reader

# 一部を削ったパターンファイルと修正前patchをdevreplayに送る
# 出力が修正後と一致すれば正解
def readPatterns() -> List[Dict[str, Any]]:  
    with open('data/changes/sstubs_devreplay_all.json', 'r') as sstubs_file:
        reader = load(sstubs_file)
        return reader


def canPatchFixable(prefixed: str, fixed: str, patterns: List[str]):
    """
    Return tha patch can be fixed the patterns
    `prefixed`, `fixed` is prefixed and fixed source code contents
    
    `pattern` is target devreplay pattern
    """
    # patch, patternをそれぞれファイルとして保存する
    prefixed_file_name = 'preFixed.java'
    pattern_file_name = 'tmpPattern.json'
    with open(prefixed_file_name, 'w', encoding='utf-8') as target:
        target.write(prefixed)
    with open(pattern_file_name, "w", encoding='utf-8') as target2:
        dump(list(reversed(patterns)), target2)

    fixed_result = execDevReplay(prefixed_file_name, pattern_file_name)

    if fixed_result.startswith(fixed):
        return 0
    if fixed_result.startswith(prefixed):
        return 1
    else:
        return -1
    # return fixed_result.startswith(fixed)


def execDevReplay(code: str, pattern: str) -> str:
    """
    Return fixed source code
    `code` is path of the prefixed source code file

    `pattern` is path of devreplay pattern file 
    """
    try:
        out = Popen(['devreplay', '--fix', code, pattern], stdin=PIPE, stdout=PIPE)
        stdout, _ = out.communicate()
    except:
        return []
    s = stdout.decode('utf-8')
    if s is None:
        return ''
    # print(s)

    return s


def getProjects(pattern: List[str]) -> List[str]:
    return list(set([x['projectName'] for x in pattern]))


def evaluatePatterns(learned_data, test_data):
    state_log = []
    total_len = len(test_data)
    init_data_len = 0
    prev_commit = ''
    prev_length = 0
    total_correct = 0
    total_suggest = 0

    for i, value in enumerate(project_data[init_data_len:], start=init_data_len):
        sys.stdout.write("\r%d/%d change" % (i, total_len))
        # コミットが前回と同じなら前回と同じ学習を使う
        learned_length = i
        if prev_commit == value['fixCommitSHA1']:
            learned_length = prev_length
        
        learned_pattern = learned_data[:learned_length]
        beforeFix = value['sourceBeforeFix']
        afterFix = value['sourceAfterFix']

        isFixed = canPatchFixable(beforeFix, afterFix, learned_pattern)
        if int(isFixed) != 1:
            total_suggest += 1
            if int(isFixed) == 0:
                total_correct += 1
        precision = '{:5.2f}'.format(total_correct / total_suggest) if total_suggest !=0 else 0
        recall = '{:5.2f}'.format(total_correct / (i+1))
        state = {
            'project': value['projectName'],
            'bugType': value['bugType'],
            'fixCommitSHA1': value['fixCommitSHA1'],
            'state': isFixed,
            'correct': total_correct,
            'precision': precision,
            'recall': recall
        }
        state_log.append(state)
        prev_commit = value['fixCommitSHA1']
        prev_length = learned_length
    return state_log

# ファイル読み込み
# out_name = f"data/changes/sstubs_devreplay.json"
# with open(out_name, "r", encoding='utf-8') as f:
#     data_set = load(f)
#     total_count = sum(x['count'] for x in data_set)
    

tp = 0
target_data = readsstubs()
target_patterns = readPatterns()
projects = getProjects(target_data)

bug_types = ['SWAP_ARGUMENTS', 'CHANGE_OPERATOR', 'CHANGE_OPERAND']
# Same Function Swap Args
# Change Binary Operator
# Change Operand Checks
for bug_type in bug_types:
    for j, project in enumerate(projects):
        # sys.stdout.write("\r%s %d/%d projects\n" % (project, j, len(projects)))
        project_data = [x for x in target_data if x['projectName'] == project and x['bugType'] == bug_type]
        project_patterns = [x for x in target_patterns if x['author'] == project and x['message'] == bug_type]

        state_log = evaluatePatterns(project_patterns, project_data)

        with open(f'data/sstubs/sstubs_{project}_{bug_type}.csv', 'w') as target:
            writer = DictWriter(target, ['project', 'bugType', 'fixCommitSHA1', 'state', 'correct', 'precision', 'recall'])
            writer.writeheader()
            writer.writerows(state_log)


# for j, project in enumerate(projects):
#     sys.stdout.write("\r%s %d/%d projects\n" % (project, j, len(projects)))
#     project_data = [x for x in target_data if x['projectName'] == project]
#     project_patterns = [x for x in target_patterns if x['author'] == project]

#     state_log = evaluatePatterns(project_patterns, project_data)

#     with open(f'data/sstubs/sstubs_{project}.csv', 'w') as target:
#         writer = DictWriter(target, ['project', 'bugType', 'fixCommitSHA1', 'state', 'correct', 'precision', 'recall'])
#         writer.writeheader()
#         writer.writerows(state_log)


