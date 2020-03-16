"""
Get popular project
Requirements:
$ touch config.json
Edit config.json
"""

import csv
import os
import sys
from json import dump, loads, dumps, load

with open("config.json", "r") as json_file:
    config = load(json_file)

with open("top_repos.csv", "r") as org_file:
    reader = csv.DictReader(org_file)

    for project in reader:
        owner = project["owner"]
        repo = project["repo"]
        branch = project["branch"]
        lang = project["lang"]

        print(owner + "/" + repo)
        with open("config.json", "w") as config_file:
            config["projects"] = [{
                "owner": owner,
                "repo": repo,
                "branch": branch
            }]
            config["lang"] = lang

            dump(config, config_file, indent=1)
        os.system("python3 collect_changes.py")
        # os.system("python3 test_rules.py")
