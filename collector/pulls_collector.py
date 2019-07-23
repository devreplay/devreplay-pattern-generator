import json
import sys
from csv import DictWriter
from datetime import datetime, timezone
from time import sleep
from typing import Generator, Optional
from urllib.error import HTTPError
from urllib.request import urlopen, Request


class PullsCollector:
    MAX_FETCH_RETRY = 3
    fields = [
        "number",
        "author",
        "participant",
        "commit_len",
        "base_commit_sha",
        "first_commit_sha",
        "merge_commit_sha",
        "created_at",
        "merged_at",
        "merged_by"
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
                if pull['commits']['totalCount'] > 0:
                    yield self._format(pull)
            if not obj['data']['repository']['pullRequests']['pageInfo']['hasNextPage']:
                break
            cursor = obj['data']['repository']['pullRequests']['pageInfo']['endCursor']
            if obj['data']['rateLimit']['remaining'] < 1:
                reset_at = self._parse_datetime(obj['data']['rateLimit']['resetAt'])
                delta = reset_at - datetime.now(timezone.utc)
                sleep(delta.seconds)

    def _fetch(self, cursor: str = None, nth_retry: int = 0) -> dict:
        req = Request(
            'https://api.github.com/graphql',
            method='POST',
            data=self._graphql_request(cursor),
            headers={
                'Authorization': f'bearer {self._token}',
            })
        try:
            response = urlopen(req)
        except HTTPError as e:
            print('===== Headers\n\n'
                  f'{e.headers.as_string()}\n'
                  '===== Reason\n\n'
                  f'{e.reason}\n\n'
                  '===== Code\n'
                  f'{e.code}\n', file=sys.stderr)
            retry_after = e.headers.get('Retry-After')
            if retry_after is not None and nth_retry < self.MAX_FETCH_RETRY:
                print(f'Waiting {retry_after} seconds to retry fetching', file=sys.stderr)
                sleep(int(retry_after))
                return self._fetch(cursor, nth_retry + 1)
            else:
                raise
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
                      author {
                        login
                      }
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
                      participants(first:100) {
                        edges {
                          node {
                            login
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
        author = pull["author"]["login"]
        commit_oids = [edge['node']['commit']['oid'] for edge in pull['commits']['edges']]
        participant = [participant["node"]["login"] for participant in pull["participants"]["edges"] 
                        if participant["node"]["login"] != author]
        base_sha = commit_oids[0]
        head_sha = commit_oids[-1]
        return {
            "author": author,
            "participant": participant[0] if len(participant) > 0 else "None",
            "number": pull['number'],
            "commit_len": pull['commits']['totalCount'],
            "base_commit_sha": pull['baseRefOid'],
            "first_commit_sha": base_sha,
            "merge_commit_sha": head_sha,
            "created_at": self._parse_datetime(pull['createdAt']),
            "merged_at": self._parse_datetime(pull['mergedAt']),
            "merged_by": self._merged_by(pull),
        }

    def _parse_datetime(self, d: str) -> datetime:
        return datetime.strptime(d, '%Y-%m-%dT%H:%M:%SZ')

    def _merged_by(self, pull: dict) -> Optional[str]:
        merged_by = pull.get('mergedBy')
        if merged_by is None:
            return None
        return merged_by.get('login')
