import json

with open("config.json", "r") as json_file:
    config = json.load(json_file)

lang = config["lang"]
projects = config["projects"]
learn_from = "pulls" if "pull" in config["learn_from"] else "master"
validate_by = "pulls" if "pull" in config["validate_by"] else "master"


input_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + ".json"
            for x in projects]
result = []
for input_file in input_files:
    print("Combine from " + input_file)
    with open(input_file, "r") as target:
        data = json.load(target)
        result.extend(data)

with open("data/changes/devreplay_" + learn_from + ".json", "w") as outfile:
    json.dump(result, outfile)

if learn_from != validate_by:
    input_files = ["data/changes/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + validate_by + ".json"
            for x in projects]
    result = []
    for input_file in input_files:
        print("Combine from " + input_file)
        with open(input_file, "r") as target:
            data = json.load(target)
            result.extend(data)

    with open("data/changes/devreplay_" + validate_by + ".json", "w") as outfile:
        json.dump(result, outfile)