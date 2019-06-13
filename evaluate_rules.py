import json
from configparser import ConfigParser

config = ConfigParser()
config.read('config')
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]
lang = config["Target"]["lang"]
threshold = [int(x) for x in config["Rule"]["thresholds"].split()][0]

RULE_JSON_NAME = "data/rules/" + owner + "_" + repo + "_"  + str(threshold) + "_" + lang + ".json"
# RULE_JSON_NAME = "pattern2.json"
CHANGE_JSON_NAME = "data/changes/" + owner + "_" + repo + "_" + lang + ".json"
EVALUATED_RULE_JSON_NAME = "data/rules/" + owner + "_" + repo + "_"  + str(threshold) + "_" + lang + "_evaluated.json"

def main():

    with open(RULE_JSON_NAME, "r") as json_file:
        rules = json.load(json_file)

    with open(CHANGE_JSON_NAME, "r") as json_file:
        changes = json.load(json_file)

    evaluated_rules = []

    for rule in rules:
        after = makeAfter(rule["code"])
        trigger = makeBefore(rule["code"])

        trigarable_changes = [x for x in changes if isTrigarable(trigger, makeBefore(x["changes_set"]))]
        rule["trigarable_len"] = len(trigarable_changes)
        if rule["trigarable_len"] == 0:
            continue

        adoptable_changes = [x for x in trigarable_changes if isTrigarable(after, makeAfter(x["changes_set"]))]
        rule["adoptable_len"] = len(adoptable_changes)
        if rule["adoptable_len"] == 0:
            continue
        rule["adoptable_pull_id"] = list(set([x["number"] for x in adoptable_changes]))
        rule["accuracy"] =  rule["adoptable_len"] / rule["trigarable_len"]
        
        if rule["accuracy"] < 0.01:
            continue

        evaluated_rules.append(rule)
    evaluated_rules = sorted(evaluated_rules, key= lambda x:x["accuracy"], reverse = True)
    if len(evaluated_rules) == 0:
        print("No rule is useful")
    evaluated_rules[0]["rule_sum"] = len(evaluated_rules)
    evaluated_rules[0]["change_sum"] = len(changes)

    with open(EVALUATED_RULE_JSON_NAME, "w") as json_file:
        json.dump(evaluated_rules, json_file, indent=2)

def makeBefore(changes):
    before_changes = []
    for change in changes:
        if change.startswith("*"):
            before = change[2:].split("-->")[0][:-1].split(" ")
            before_changes.extend(before)
        elif not change.startswith("+"):
            before_changes.extend(change[2:].split(" "))
    return before_changes

def makeAfter(changes):
    after_changes = []
    for change in changes:
        if change.startswith("*"):
            after = change[2:].split("-->")[1][1:].split(" ")
            after_changes.extend(after)
        elif not change.startswith("="):
            after_changes.extend(change[2:].split(" "))
    return after_changes


def isTrigarable(rule, code):
    code_index = 0
    for i in rule:
        founded = False
        for j, b in enumerate(code[code_index:], 1):
            if b == i:
                founded = True
                code_index += j
                break
        if not founded:
            return False
    return True

if __name__ == "__main__":
    main()
