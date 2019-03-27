from json import dump, load
from configparser import ConfigParser
from difflib import ndiff
from prefixspan import PrefixSpan_frequent, PrefixSpan

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]

INPUT_JSON_NAME = "changes/" + owner + "_" + repo + "_" + lang + ".json"
OUTPUT_JSON_NAME = "rules/" + owner + "_" + repo + "_" + lang + ".json"


with open(INPUT_JSON_NAME, mode='r', encoding='utf-8') as f:
    changes_sets = load(f)

changes = [x["changes_set"] for x in changes_sets]

new_changes = []
for tokens in changes:
    new_tokens = [x for x in tokens
                  if not x.endswith("\n") and not x.endswith(" ")]
    if new_tokens != [] and new_tokens not in new_changes:
        new_changes.append(new_tokens)

print("Start rule generation")
ps = PrefixSpan(new_changes)
freq_seqs = ps.frequent(minsup=int(len(new_changes) * 0.1), closed=True)
# freq_seqs = PrefixSpan_frequent(
#     ps, minsup=int(len(new_changes) * 0.1), closed=True)
freq_seqs = [x for x in freq_seqs
             if any([y.startswith("+") for y in x[1]]) and
             any([y.startswith("-") for y in x[1]])
             ]

freq_seqs = sorted(freq_seqs, reverse=True)

with open(OUTPUT_JSON_NAME, mode='w', encoding='utf-8') as f:
    dump(freq_seqs, f, indent=1)
