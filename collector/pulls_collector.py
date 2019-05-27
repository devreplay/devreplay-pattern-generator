import json
from csv import DictWriter
from datetime import datetime, timezone
from time import sleep
from typing import Generator
from urllib.request import urlopen, Request


class PullsCollector:
    fields = [
        "number",
        "commit_len",
        "base_commit_sha",
        "first_commit_sha",
        "merge_commit_sha",
        "created_at",
        "merged_at",
        "merged_by",
        "1-n_url"
    ]

    def __init__(self, token: str, repo_owner: str, repo_name: str):
        self._token = token
        self._repo_owner = repo_owner
        self._repo_name = repo_name

    def save_all(self, output_path: str):
        with open(output_path, 'w', encoding='utf-8', buffering=1) as f:
            writer = DictWriter(f, self.fields)
            writer.writeheader()
            for row in self.all():
                writer.writerow(row)

    def all(self) -> Generator:
        cursor = None

        while True:
            obj = self._fetch(cursor)
            for pull in (edge['node'] for edge in obj['data']['repository']['pullRequests']['edges']):
                yield self._format(pull)
            if not obj['data']['repository']['pullRequests']['pageInfo']['hasNextPage']:
                break
            cursor = obj['data']['repository']['pullRequests']['pageInfo']['endCursor']
            if obj['data']['rateLimit']['remaining'] < 1:
                reset_at = self._parse_datetime(obj['data']['rateLimit']['resetAt'])
                delta = reset_at - datetime.now(timezone.utc)
                sleep(delta.seconds)

    def _fetch(self, cursor: str = None) -> dict:
        req = Request(
            'https://api.github.com/graphql',
            method='POST',
            data=self._graphql_request(cursor),
            headers={
                'Authorization': f'bearer {self._token}',
            })
        response = urlopen(req)
        return json.loads(response.read().decode('utf-8'))

    def _graphql_request(self, cursor: str = None) -> str:
        """GitHub GraphQL Query

        See https://developer.github.com/v4/object/pullrequest/
        """
        query = '''
            query($cursor: String) {
              rateLimit {
                remaining
                resetAt
              }
              repository(owner: "%(repo_owner)s", name: "%(repo_name)s") {
                pullRequests(after: $cursor, first: 100, baseRefName: "master", states: [MERGED], orderBy: {field: CREATED_AT, direction: ASC}) {
                  pageInfo {
                    hasNextPage
                    endCursor
                  }
                  edges {
                    node {
                      number
                      createdAt
                      mergedAt
                      mergedBy {
                        login
                      }
                      baseRefOid
                      commits(first:100) {
                        totalCount
                        edges {
                          node {
                            commit {
                              oid
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }
            }
        ''' % {'repo_owner': self._repo_owner, 'repo_name': self._repo_name}
        return json.dumps({'query': query, 'variables': {'cursor': cursor}}).encode('utf-8')

    def _format(self, pull: dict) -> dict:
        commit_oids = [edge['node']['commit']['oid'] for edge in pull['commits']['edges']]
        base_sha = commit_oids[0]
        head_sha = commit_oids[-1]
        return {
            "number": pull['number'],
            "commit_len": pull['commits']['totalCount'],
            "base_commit_sha": pull['baseRefOid'],
            "first_commit_sha": base_sha,
            "merge_commit_sha": head_sha,
            "1-n_url": self._compare_url(base_sha, head_sha),
            "created_at": self._parse_datetime(pull['createdAt']),
            "merged_at": self._parse_datetime(pull['mergedAt']),
            "merged_by": pull['mergedBy']['login'],
        }

    def _parse_datetime(self, d: str) -> datetime:
        return datetime.strptime(d, '%Y-%m-%dT%H:%M:%S%z')

    def _compare_url(self, base: str, head: str) -> str:
        return f'https://github.com/{self._repo_owner}/{self._repo_name}/compare/{base}...{head}.diff'
