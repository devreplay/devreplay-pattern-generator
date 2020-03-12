#%%
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import csv
import json
#%%
with open("config.json", "r") as json_file:
    config = json.load(json_file)

lang = config["lang"]

def get_projects(path):
    with open(path, "r") as json_file:
        projects = json.load(json_file)
        return [x for x in list(projects) if "language" not in x or x["language"] == lang]

if "projects_path" in config:
    projects = get_projects(config["projects_path"])
else:
    projects = config["projects"]
learn_from = "pulls" if "pull" in config["learn_from"] else "master"

from_self = True

if from_self:
    out_files = {x["repo"]: "data/result/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + ".csv"
                for x in projects}
else:
    out_files = {x["repo"]: "data/result/" + x["owner"] + "_" + x["repo"] + "_" + lang  + "_"  + learn_from + "_cross.csv"
                for x in projects}
#%%
def makeResultData(path, project):
    with open(path, "r") as target:
        result = list(csv.DictReader(target))
        result = pd.DataFrame(result)

    result = result.astype({"suggested_num": "int32",
                            "learned_num": "int32",
                            "rule_index": "int32"})
    result = result.assign(project = [project for x in result.itertuples()])
    result = result.assign(state = ["same" if x.success == "True" else "no rule" if x.suggested_num == 0 else "different" for x in result.itertuples()])
    return result

#%%
all_result = pd.DataFrame([])
for project, pro_path in out_files.items():
    tmp_result = makeResultData(pro_path, project)
    all_result = pd.concat([tmp_result, all_result])
result = all_result
print(len(result[result["state"]=="same"]))
print(len(result[result["state"]=="different"]))
print(len(result[result["state"]=="no rule"]))
#%%
table = pd.crosstab(result["project"], result["state"])
print(table.to_latex())
# %%
