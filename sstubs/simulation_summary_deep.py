from json import load
from os import name
from typing import Any, DefaultDict, Dict, List
from csv import DictReader, DictWriter
import sys
import pandas as pd


def readsstubs() -> List[Dict[str, Any]]:
    with open('data/sstubs/sstubs.json', 'r') as sstubs_file:
        reader = load(sstubs_file)
        return reader

def getProjects(pattern: List[str]) -> List[str]:
    return list(set([x['projectName'] for x in pattern]))

def getBugTypes(pattern: List[str]) -> List[str]:
    return list(set([x['bugType'] for x in pattern]))

def makeKlearned(patterns, k: int):
    patterns_len = len(patterns)
    learned_len = int(patterns_len / k)

    total_suggest = 0
    total_correct = 0
    fixed_patterns = []
    for i, pattern in enumerate(patterns[learned_len:]):
        isFixed = int(pattern['state'])
        if isFixed != 1:
            total_suggest += 1
            if isFixed == 0:
                total_correct += 1
        precision = '{:5.2f}'.format(total_correct / total_suggest) if total_suggest !=0 else 0
        recall = '{:5.2f}'.format(total_correct / (i+1))
        pattern[f'{k}_correct'] = total_correct
        pattern[f'{k}_precision'] = precision
        pattern[f'{k}_recall'] = recall
        fixed_patterns.append(pattern)
    return fixed_patterns


def correctBugTypeSummary(projects: List[str], bugTypes: List[str], K: int):
    bugTypeOut = {}
    k_bugTypeOut = {}

    for project in projects:
        # sys.stdout.write("\r%s %d/%d projects\n" % (project, j, len(projects)))

        for bugType in bugTypes:
            with open(f'data/sstubs/sstubs_{project}_{bugType}.csv', 'r') as target:
                # names = ['project', 'bugType', 'fixCommitSHA1', 'state', 'correct', 'precision', 'recall']
                reader = list(DictReader(target))
                bugTypeCollect = [x for x in reader if x['bugType'] == bugType]
                if bugType in bugTypeOut:
                    bugTypeOut[bugType]['size'] += len(bugTypeCollect)
                    bugTypeOut[bugType]['correct'] += len([x for x in bugTypeCollect if int(x['state']) == 0])
                    bugTypeOut[bugType]['suggest'] += len([x for x in bugTypeCollect if int(x['state']) in [0, 1]])
                else:
                    bugTypeOut[bugType] = {
                        'size': len(bugTypeCollect),
                        'correct': len([x for x in bugTypeCollect if int(x['state']) == 0]),
                        'suggest': len([x for x in bugTypeCollect if int(x['state']) in [0, 1]])
                    }
                k_reader = makeKlearned(bugTypeCollect, K)
                if bugType in k_bugTypeOut:
                    k_bugTypeOut[bugType]['size'] += len(k_reader)
                    k_bugTypeOut[bugType]['correct'] += len([x for x in k_reader if int(x['state']) == 0])
                    k_bugTypeOut[bugType]['suggest'] += len([x for x in k_reader if int(x['state']) in [0, 1]])
                else:
                    k_bugTypeOut[bugType] = {
                        'size': len(k_reader),
                        'correct': len([x for x in k_reader if int(x['state']) == 0]),
                        'suggest': len([x for x in k_reader if int(x['state']) in [0, 1]])
                        }

    output = []
    total = 0
    total_fixed = 0
    total_suggest = 0

    k_total = 0
    k_total_fixed = 0
    k_total_suggest = 0
    for bugType in bugTypes:
        output.append({
            'bugType': bugType,
            'size': bugTypeOut[bugType]['size'],
            'correct': bugTypeOut[bugType]['correct'],
            'suggest': bugTypeOut[bugType]['suggest'],
            'precision': bugTypeOut[bugType]['correct'] / bugTypeOut[bugType]['suggest'],
            'recall': bugTypeOut[bugType]['correct'] / bugTypeOut[bugType]['size'],
            f'{K}_precision': k_bugTypeOut[bugType]['correct'] / k_bugTypeOut[bugType]['suggest'],
            f'{K}_recall': k_bugTypeOut[bugType]['correct'] / k_bugTypeOut[bugType]['size']
        })
        total += bugTypeOut[bugType]['size']
        total_fixed += bugTypeOut[bugType]['correct']
        total_suggest +=bugTypeOut[bugType]['suggest']

        k_total += k_bugTypeOut[bugType]['size']
        k_total_fixed += k_bugTypeOut[bugType]['correct']
        k_total_suggest +=k_bugTypeOut[bugType]['suggest']

    output = sorted(output, key=lambda x: x['recall'], reverse=True)

    total_sum = {
        'bugType': 'all',
        'size': total,
        'correct': total_fixed,
        'suggest': total_suggest,
        'precision': total_fixed / total_suggest,
        'recall': total_fixed / total,
        f'{K}_precision': k_total_fixed / k_total_suggest,
        f'{K}_recall': k_total_fixed / k_total
    }
    output = [total_sum] + output

    return output


target_data = readsstubs()
projects = getProjects(target_data)
bugTypes = getBugTypes(target_data)
bugTypes = ['SWAP_ARGUMENTS', 'CHANGE_OPERATOR', 'CHANGE_OPERAND']

K = 10

filter_size = 0
filtered_projects = []

for project in projects:
    # sys.stdout.write("\r%s %d/%d projects\n" % (project, j, len(projects)))
    with open(f'data/sstubs/sstubs_{project}.csv', 'r') as target:
        # names = ['project', 'bugType', 'fixCommitSHA1', 'state', 'correct', 'precision', 'recall']
        reader = list(DictReader(target))
        if len(reader) > filter_size:
            filtered_projects.append(project)

projects = filtered_projects

output = correctBugTypeSummary(projects, bugTypes, K)
with open(f'data/sstubs/F{filter_size}K{K}_bug_summary_deep.csv', 'w') as target:
    writer = DictWriter(target, ['bugType', 'size', 'correct', 'suggest','precision', 'recall', f'{K}_precision', f'{K}_recall'])
    writer.writeheader()
    writer.writerows(output)