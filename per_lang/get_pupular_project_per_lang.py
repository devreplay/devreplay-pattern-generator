"""
Get popular project
Before run
$ pip3 install PyGithub
$ touch config.json
Edit config.sjon
"""

import requests
import json
import csv
from github import Github
import configparser

config = configparser.ConfigParser()
config.read('config')
user = config["GitHub"]["id"]
password = config["GitHub"]["password"]
g = Github(user, password)
languages = ["Python", "Java", "JavaScript", "C++", "Ruby"]

for language in languages:
    repos = g.search_repositories("stars:>0", sort="stars", language=language)

    results = []
    for x in repos[:10]:
        results.append({"repo": x.name, "owner": x.owner.login,
                        "url": x.url, "forks": x.forks, "stars": x.stargazers_count})

    with open("data/popular_" + language + ".csv", "w") as org_file:
        writer = csv.DictWriter(
            org_file, ["repo", "owner", "url", "forks", "stars"])
        writer.writeheader()
        writer.writerows(results)