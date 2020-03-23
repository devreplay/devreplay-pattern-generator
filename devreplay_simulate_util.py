import re
import os

group_changes = re.compile(r"\\\$\\{(\d+):[a-zA-Z_]+\\}")
group_changes2 = re.compile(r"\$\{(\d+):[a-zA-Z_]+\}")
consequent_newline = re.compile(r"(\".+\\)(n.*\")")

def is_meaninglines(line):
    return not (line.isspace() or line.lstrip().startswith("//"))

def group2increment(matchobj, identifier_ids):
    tokenid = int(matchobj.group(1))
    if tokenid in identifier_ids:
        return r"(?P=token" + str(tokenid + 1) + r")"
    else:
        identifier_ids.append(tokenid)
        return r"(?P<token" + str(tokenid + 1) + r">\"[\w\s_]+\"|[\w]+)"

def snippet2Regex(snippet):
    identifier_ids = []
    joinedCondition = "\n".join([re.escape(x) for x in snippet])
    joinedCondition = group_changes.sub(lambda m: group2increment(m, identifier_ids), joinedCondition)
    try:
        return re.compile(joinedCondition)
    except:
        return

def consequent2regex(matchobj, identifier_ids):
    tokenid = int(matchobj.group(1))
    return r"\g<token" + str(tokenid + 1) +r">"

def snippet2RegexConsequent(snippet):
    identifier_ids = []
    joinedCondition = "\n".join(snippet)
    joinedCondition = consequent_newline.sub(r"\g<1>\\\g<2>", joinedCondition)
    return group_changes2.sub(lambda m: consequent2regex(m, identifier_ids), joinedCondition)

def snippet2RegexCondition(snippet):
    identifier_ids = []
    joinedCondition = "\n".join([re.escape(x) for x in snippet])
    joinedCondition = group_changes.sub(lambda m: group2increment(m, identifier_ids), joinedCondition)
    try:
        return re.compile(joinedCondition)
    except:
        exit()

def snippet2Realcode(snippet, abstracted):
    return group_changes2.sub(lambda m: abstracted[m.group(1)], "\n".join(snippet))


def buggy2accepted(buggy, rules, rule_size):
    tmp_rules = [x for x in rules if x["re_condition"].search(buggy)]
    if not tmp_rules:
        return []
    else:
        result = []
        for rule in tmp_rules:
            fixed_content = rule["re_condition"].sub(rule["re_consequent"], buggy)
            if fixed_content == buggy:
                continue

            result.append(fixed_content)
        return result

def buggy2accepted_id(buggy, rules, rule_size):
    tmp_rules = [x for x in rules if x["re_condition"].search(buggy)]
    if not tmp_rules:
        return []
    else:
        result = []
        for rule in tmp_rules:
            try:
                fixed_content = rule["re_condition"].sub(rule["re_consequent"], buggy)
            except Exception as e:
                print(e)
                continue
            if fixed_content == buggy:
                continue

            result.append((fixed_content.strip(), rule["sha"]))
        return result
