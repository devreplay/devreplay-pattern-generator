from prefixspan import PrefixSpan_frequent, PrefixSpan_topk, PrefixSpan
import json
import configparser
from difflib import ndiff

config = configparser.ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]

INPUT_JSON_NAME = "changes/" + owner + "_" + repo + "_" + lang + "2.json"
OUTPUT_JSON_NAME = "rules/" + owner + "_" + repo + "_" + lang + ".json"


with open(INPUT_JSON_NAME, mode='r', encoding='utf-8') as f:
    changes_sets = json.load(f)

changes = [x["changes_sets"] for x in changes_sets]

ps = PrefixSpan(changes)
freq_seqs = PrefixSpan_frequent(ps, minsup = int(len(changes) * 0.1), closed=True)
freq_seqs = [x for x in freq_seqs
if any([y.startswith("+") for y in x[1]]) and
any([y.startswith("-") for y in x[1]])
]

freq_seqs = sorted(freq_seqs, reverse=True)

with open(OUTPUT_JSON_NAME, mode='w', encoding='utf-8') as f:
    json.dump(freq_seqs, f, indent=1)
