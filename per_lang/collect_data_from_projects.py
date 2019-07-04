"""
Get popular project
Before run
$ pip3 install PyGithub
$ touch config.json
Edit config.sjon
"""

import json
import csv
import os
import configparser
import sys
# import collect_pulls
# import collect_changes_clone
# import merge_changes

config = configparser.ConfigParser()
config.read('config')
user = config["GitHub"]["id"]
password = config["GitHub"]["password"]
language = config["Target"]["lang"]



with open("data/popular_" + language + ".csv", "r") as org_file:
    reader = csv.DictReader(org_file)
    for project in reader:
        owner = project["owner"]
        repo = project["repo"]
        print(owner + "/" + repo)
        with open("config", "w") as config_file:
            new_config = config
            config.set("Target", "owner", owner)
            config.set("Target", "repo", repo)
            config.write(config_file)
        os.system("python3 collect_pulls.py")
        os.system("python3 collect_changes_clone.py")
        os.system("python3 merge_changes.py")
