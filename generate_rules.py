from json import dump, load
from configparser import ConfigParser
from difflib import ndiff
from prefixspan import PrefixSpan_frequent, PrefixSpan
import np

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]

INPUT_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + ".json"
OUTPUT_JSON_NAME = "data/rules/" + owner + "_" + repo + "_" + lang + ".json"


def remove_dup_changes(changes_sets):
    new_changes = []
    current_pull = 0
    for changes_set in changes_sets:
        if current_pull == changes_set["number"] and\
                changes_set["changes_set"] in new_changes:
            continue
        current_pull = changes_set["number"]
        new_changes.append(changes_set["changes_set"])
    return new_changes


def generate_rules(changes_sets, threshold):
    ps = PrefixSpan(changes_sets)
    print("Start rule generation")
    # freq_seqs = ps.frequent(minsup=int(len(new_changes) * 0.1), closed=True)
    freq_seqs = ps.frequent(minsup=threshold, closed=True)

    # freq_seqs = PrefixSpan_frequent(
    #     ps, minsup=int(len(new_changes) * 0.1), closed=True)
    freq_seqs = [x for x in freq_seqs
                 if any([y.startswith("+") for y in x[1]]) and
                 any([y.startswith("-") for y in x[1]])
                 ]

    freq_seqs = sorted(freq_seqs, reverse=True)
    return freq_seqs

with open(INPUT_JSON_NAME, mode='r', encoding='utf-8') as f:
    changes_sets = load(f)

changes = remove_dup_changes(changes_sets)

# new_changes = []
# for tokens in changes:
#     new_tokens = [x for x in tokens
#                   if not x.endswith("\n") and not x.endswith(" ")]
#     if new_tokens != []:
#         new_changes.append(new_tokens)

changes = [[x for x in tokens
            if not x.endswith("\n") and not x.endswith(" ")]
           for tokens in changes]

freq_seqs = generate_rules(changes, 7)

new_rules = []

for i, rule in enumerate(freq_seqs):
    count = rule[0]
    code = rule[1]
    trigger_tokens = list(np.hstack([x[2:].split(" ") if " " in x[2:] else [x[2:]] for x in code if not x.startswith("+")]))
    new_rules.append({"count": count, "code": code, "trigger": trigger_tokens})

with open(OUTPUT_JSON_NAME, mode='w', encoding='utf-8') as f:
    dump(new_rules, f, indent=1)
