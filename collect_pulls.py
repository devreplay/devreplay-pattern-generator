"""
Usage: python3 collect_pulls.py
"""
import configparser

from review_pattern_gen.pulls_collector import PullsCollector

config = configparser.ConfigParser()
config.read('config')
token = config["GitHub"].get("token")
owner = config["Target"]["owner"]
repo = config["Target"]["repo"]

collector = PullsCollector(token, owner, repo)
collector.save_all(f'data/pulls/{owner}_{repo}.csv')
