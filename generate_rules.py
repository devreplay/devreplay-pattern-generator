from prefixspan import PrefixSpan_frequent, PrefixSpan_topk, PrefixSpan
import json

INPUT_JSON_NAME = "data/orgs/diffs/Microsoft_code.json"
OUTPUT_JSON_NAME = "data/orgs/diffs/Microsoft_rule.json"

with open(INPUT_JSON_NAME, mode='r', encoding='utf-8') as f:
    changes_sets = json.load(f)

changes = [x["code"] for x in changes_sets]

# freq_seqs = seqmining.freq_seq_enum(changes, 2)
ps = PrefixSpan(changes)
freq_seqs = PrefixSpan_frequent(ps, minsup = 100, closed=True)
freq_seqs = [x for x in freq_seqs
if any([y.startswith("+") for y in x[1]]) and
any([y.startswith("-") for y in x[1]])
]
# freq_seqs = PrefixSpan_topk(ps, 15, closed=True)
# freq_seqs = [{"code": x[0], "count": x[1]} for x in freq_seqs\
#  if "***" in x[0] and \
#  x[0].index("***") not in [0, len(x[0]) - 1] ]

freq_seqs = sorted(freq_seqs, reverse=True)

with open(OUTPUT_JSON_NAME, mode='w', encoding='utf-8') as f:
    json.dump(freq_seqs, f, indent=2)

