import unittest

from depoverflow.github import GithubIssue, GithubPullRequest
from depoverflow.stackexchange import StackExchangeQuestion, \
    StackExchangeAnswer
from depoverflow.utils import batch


class TestReferences(unittest.TestCase):
    def test_github_issue(self):
        self.assertTrue(GithubIssue.is_url_reference(
            'https://github.com/remram44/depoverflow/issues/1',
        ))
        self.assertFalse(GithubIssue.is_url_reference(
            'http://github.com/remram44/depoverflow/pull/21',
        ))
        self.assertFalse(GithubIssue.is_url_reference(
            'https://github.com/remram44/depoverflow/issues',
        ))

        issue = GithubIssue.create(
            'http://github.com/remram44/depoverflow/issues/1'
        )
        self.assertEqual(
            (issue.TYPE, issue.repo, issue.number),
            ('github-issue', 'remram44/depoverflow', 1),
        )

    def test_github_pr(self):
        self.assertFalse(GithubPullRequest.is_url_reference(
            'https://github.com/remram44/depoverflow/issues/21',
        ))
        self.assertTrue(GithubPullRequest.is_url_reference(
            'http://github.com/remram44/depoverflow/pull/1',
        ))
        self.assertFalse(GithubPullRequest.is_url_reference(
            'https://github.com/remram44/depoverflow/pulls',
        ))

        issue = GithubPullRequest.create(
            'http://github.com/remram44/depoverflow/pull/21'
        )
        self.assertEqual(
            (issue.TYPE, issue.repo, issue.number),
            ('github-pr', 'remram44/depoverflow', 21),
        )

    def test_stackexchange_question(self):
        self.assertTrue(StackExchangeQuestion.is_url_reference(
            'https://stackoverflow.com/questions/44990227/'
            + 'forwarding-from-a-futuresstream-to-a-futuressink',
        ))
        self.assertTrue(StackExchangeQuestion.is_url_reference(
            'https://stackoverflow.com/questions/44990227/',
        ))
        self.assertTrue(StackExchangeQuestion.is_url_reference(
            'https://stackoverflow.com/questions/44990227',
        ))
        self.assertTrue(StackExchangeQuestion.is_url_reference(
            'https://stackoverflow.com/q/44990227',
        ))
        self.assertTrue(StackExchangeQuestion.is_url_reference(
            'https://stackoverflow.com/q/44990227/711380',
        ))

        question = StackExchangeQuestion.create(
            'https://stackoverflow.com/q/44990227/711380',
        )
        self.assertEqual(
            (question.TYPE, question.site, question.id),
            ('stackexchange-question', 'stackoverflow.com', 44990227),
        )

    def test_stackexchange_answer(self):
        self.assertTrue(StackExchangeAnswer.is_url_reference(
            'https://stackoverflow.com/a/13445719/711380',
        ))
        self.assertTrue(StackExchangeAnswer.is_url_reference(
            'https://stackoverflow.com/a/13445719/',
        ))
        self.assertTrue(StackExchangeAnswer.is_url_reference(
            'https://stackoverflow.com/a/13445719',
        ))

        answer = StackExchangeAnswer.create(
            'https://stackoverflow.com/a/13445719/711380',
        )
        self.assertEqual(
            (answer.TYPE, answer.site, answer.id),
            ('stackexchange-answer', 'stackoverflow.com', 13445719),
        )


class TestUtils(unittest.TestCase):
    def test_batch(self):
        self.assertEqual(
            list(batch([1, 2, 3, 4, 5, 6, 7], 3)),
            [[1, 2, 3], [4, 5, 6], [7]],
        )
        self.assertEqual(
            list(batch([1, 2, 3, 4, 5, 6], 3)),
            [[1, 2, 3], [4, 5, 6]],
        )


if __name__ == '__main__':
    unittest.main()
