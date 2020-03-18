from json import dump, loads, dumps, load

with open("config.json", "r") as json_file:
    config = load(json_file)

lang = config["lang"]
projects = projects = config["projects"]
learn_from = config["learn_from"]

OUT_TOKEN_NAME = "data/changes/" + projects[0]["owner"] + "_" + projects[0]["repo"] + \
"_" + lang + "_" + learn_from + "_devreplay.json"
OUT_TOKEN_NAME3 = "data/changes/" + projects[0]["owner"] + "_" + projects[0]["repo"] + \
"_" + lang + "_" + learn_from + "_devreplay3.json"
output = []

with open(OUT_TOKEN_NAME, "r") as jsonfile:
    target_changes = json.load(jsonfile)
    for i, change in enumerate(target_changes):
        change["id"] = i
        output.append(change)

with open(OUT_TOKEN_NAME3, "w") as target:
    print("Success to validate the changes Output is " + OUT_TOKEN_NAME3)
    json.dump(output, target, indent=2)
