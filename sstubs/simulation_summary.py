from json import load
from os import name
from typing import Any, Dict, List
from csv import DictReader, DictWriter
import sys
import pandas as pd


def readsstubs() -> List[Dict[str, Any]]:
    with open('data/sstubs/sstubs.json', 'r') as sstubs_file:
        reader = load(sstubs_file)
        return reader

def getProjects(pattern: List[str]) -> List[str]:
    return list(set([x['projectName'] for x in pattern]))

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


target_data = readsstubs()
projects = getProjects(target_data)

output = []
total = 0
total_fixed = 0

K_total = 0
K_total_fixed = 0
K = 10

for j, project in enumerate(projects):
    # sys.stdout.write("\r%s %d/%d projects\n" % (project, j, len(projects)))
    with open(f'data/sstubs/sstubs_{project}.csv', 'r') as target:
        names = ['project', 'bugType', 'fixCommitSHA1', 'state', 'correct', 'precision', 'recall']
        reader = list(DictReader(target))
        last_row = reader[-1]
        tmp_output = {
            'project': project,
            'size': len(reader),
            'precision': float(last_row['precision']),
            'recall': float(last_row['recall']),
        }
        total += len(reader)
        total_fixed += int(last_row['correct'])

        k_reader = makeKlearned(reader, K)
        last_row = k_reader[-1]

        tmp_output[f'{K}_precision'] = last_row[f'{K}_precision']
        tmp_output[f'{K}_recall'] = last_row[f'{K}_recall']
        
        K_total += len(k_reader)
        K_total_fixed += int(last_row['correct'])

        output.append(tmp_output)

output = sorted(output, key=lambda x: x['recall'], reverse=True)
total_sum = {
    'project': 'all',
    'size': total,
    'precision': 0,
    'recall': total_fixed / total,
    f'{K}_precision': 0,
    f'{K}_recall': K_total_fixed / K_total,
}
output = [total_sum] + output
with open(f'data/sstubs/summary.csv', 'w') as target:
    writer = DictWriter(target, ['project', 'size', 'precision', 'recall', f'{K}_precision', f'{K}_recall'])
    writer.writeheader()
    writer.writerows(output)
