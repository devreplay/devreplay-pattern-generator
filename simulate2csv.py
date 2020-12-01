import csv
import json

with open("config.json", "r") as json_file:
    config = json.load(json_file)



projects = {}
with open("top_repos.csv", "r") as org_file:
    reader = csv.DictReader(org_file)

    for project in reader:
        projects[project["owner"]] = "data/result/" + project["owner"] + "_" + project["repo"] + "_" + project["lang"] + "_pulls"

print(projects)

days_span = [30]


output = {}
for project, pro_path in projects.items():
    output[project] = {"project": project}
    for days in days_span:
        OUT_TOKEN_NAME = f"{pro_path}_{days}.csv"
        with open(OUT_TOKEN_NAME, "r") as result_file:
            result = list(csv.DictReader(result_file))

            suggested = [x for x in result if x["suggested_num"] != "0"]
            successed = [x["reffered_sha"] for x in suggested if x["success"] == "True"]
            unique_rules = list(set(successed))

            coveradge = len(successed) / len(result)
            precision = "{:.2%}".format(len(successed) / len(suggested))
            output[project][days] = f"{len(successed)}/{len(suggested)} ({precision})"
            output[project]["#"] = len(result)

with open("codereview_result.csv", "w") as org_file:
    writer = csv.DictWriter(org_file, ["project", "#"] + days_span)
    writer.writeheader()
    for pro_result in output.values():
        writer.writerow(pro_result)

print(output)