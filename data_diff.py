import json
import difflib
import sys

org = "Microsoft"


INPUT_JSON_NAME = "data/orgs/diffs/" + org + ".json"
DATA_FILENAME = "data/orgs/diffs/" + org + "_code.json"

with open(INPUT_JSON_NAME, mode='r', encoding='utf-8') as f:
    changes_sets = json.load(f)

changes = []
with open(DATA_FILENAME, mode='w', encoding='utf-8') as feedsjson:
    feedsjson.write("[]")

# 同一パッチの同一変更を取り除く
current_rev_change_id = 0
all_change_set = []
current_change_set = []
d = difflib.Differ()

for i, x in enumerate(changes_sets):
    a = x["change_set"]["a"]
    b = x["change_set"]["b"]
    rev_change_id = x["pull_id"]

    if a == b:
        continue

    if current_rev_change_id != rev_change_id:
        current_rev_change_id = rev_change_id
        current_change_set = []

    changed_code = []
    # current_symbol = None
    current_changes = ""
    for j in d.compare(a, b):
        if j.startswith("?"):
            continue
        # if current_symbol == j[0]:
        #     current_changes += " " + j[2:]
        # else:
        # current_symbol = j[0]
        changed_code.append(current_changes)
        current_changes = j
    changed_code.append(current_changes)

    is_same_code = any([x == changed_code for x in current_change_set])

    if is_same_code or a == b:
        continue
    else:
        current_change_set.append(changed_code)

    entry = {'chunk_id': i, 'rev_change_id': int(rev_change_id), 'code': changed_code[1:]}
    all_change_set.append(entry)
    # data.append(entry)


    # with open(DATA_FILENAME, mode='r', encoding='utf-8') as f:
    #     data = json.load(f)
with open(DATA_FILENAME, mode='w', encoding='utf-8') as feedsjson:
    json.dump(all_change_set, feedsjson, indent=2)
