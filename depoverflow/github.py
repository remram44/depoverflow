import re
import requests

from .base import Item, InvalidReference


re_issue = re.compile(
    r'^https?://github\.com/([^/]+/[^/]+)/issues/([0-9]+)/?$'
)

re_pull_request = re.compile(
    r'^https?://github\.com/([^/]+/[^/]+)/pull/([0-9]+)/?$'
)


class GithubBase(Item):
    """A GitHub issue or pull request.
    """
    def __init__(self, repo, number):
        self.repo = repo
        self.number = number
        self.updated_date = None

    def __eq__(self, other):
        return (
            self.TYPE == other.TYPE
            and self.repo == other.repo
            and self.number == other.number
        )

    def __hash__(self):
        return hash(
            (self.TYPE, self.repo, self.number),
        )

    def refresh(self):
        changed = False

        req = requests.get(
            'https://api.github.com/repos/{repo}/issues/{number}'.format(
                repo=self.repo,
                number=self.number,
            ),
        )
        req.raise_for_status()
        updated_date = req.json()['updated_at']
        if self.updated_date != updated_date:
            self.updated_date = updated_date
            changed = True

        return changed

    @classmethod
    def from_json(cls, obj):
        assert obj.keys() <= {'repo', 'number', 'updated_date'}
        item = cls(obj['repo'], obj['number'])
        item.updated_date = obj.get('updated_date')
        return item

    def to_json(self):
        return {
            'repo': self.repo,
            'number': self.number,
            'updated_date': self.updated_date,
        }


class GithubIssue(GithubBase):
    """A GitHub issue, that can be watched for comments and status changes.
    """
    TYPE = 'github-issue'

    @classmethod
    def is_url_reference(cls, url):
        m = re_issue.match(url)
        return m is not None

    @classmethod
    def create(cls, url):
        m = re_issue.match(url)
        if m is None:
            raise InvalidReference
        repo, number = m.groups()
        number = int(number)
        return cls(repo, number)

    def url(self):
        return 'https://github.com/{repo}/issues/{number}'.format(
            repo=self.repo,
            number=self.number,
        )


class GithubPullRequest(GithubBase):
    """A GitHub PR, that can be watched for comments and status changes.
    """
    TYPE = 'github-pr'

    @classmethod
    def is_url_reference(cls, url):
        m = re_pull_request.match(url)
        return m is not None

    @classmethod
    def create(cls, url):
        m = re_pull_request.match(url)
        if m is None:
            raise InvalidReference
        repo, number = m.groups()
        number = int(number)
        return cls(repo, number)

    def url(self):
        return 'https://github.com/{repo}/pull/{number}'.format(
            repo=self.repo,
            number=self.number,
        )
