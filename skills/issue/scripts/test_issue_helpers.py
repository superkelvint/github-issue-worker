import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import claim_issue
import create_worktree
import find_issues
import release_issue


def cp(code=0, out="", err=""):
    return subprocess.CompletedProcess([], code, stdout=out, stderr=err)


class FindIssuesTests(unittest.TestCase):
    def test_priority_rank_orders_p0_before_p3_and_unclassified(self):
        self.assertLess(find_issues.priority_rank({"priority:p0"}), find_issues.priority_rank({"priority:p3"}))
        self.assertLess(find_issues.priority_rank({"priority:p3"}), find_issues.priority_rank(set()))

    def test_main_uses_ready_queue_and_sorts_priority_then_age(self):
        issues = [
            {"number": 3, "createdAt": "2026-01-01T00:00:00Z", "labels": [{"name": "status:ready"}, {"name": "priority:p2"}]},
            {"number": 2, "createdAt": "2026-03-01T00:00:00Z", "labels": [{"name": "status:ready"}, {"name": "priority:p0"}]},
            {"number": 1, "createdAt": "2026-02-01T00:00:00Z", "labels": [{"name": "status:ready"}, {"name": "priority:p0"}]},
            {"number": 4, "createdAt": "2026-01-01T00:00:00Z", "labels": [{"name": "status:ready"}, {"name": "status:in-progress"}]},
        ]
        seen = {}

        def fake_gh_json(*args):
            seen["args"] = args
            return issues

        with patch.object(find_issues, "gh_json", side_effect=fake_gh_json), patch.object(
            sys, "argv", ["find", "--repo", "o/r", "--query", "schema"]
        ), patch("sys.stdout", new_callable=io.StringIO) as out:
            self.assertEqual(find_issues.main(), 0)

        data = json.loads(out.getvalue())
        self.assertEqual([x["number"] for x in data["eligible"]], [1, 2, 3])
        self.assertEqual(data["invalid"][0]["number"], 4)
        self.assertIn('label:"status:ready" schema', seen["args"])

    def test_limit_out_of_range_fails_before_query(self):
        with patch.object(sys, "argv", ["find", "--repo", "o/r", "--limit", "0"]):
            with self.assertRaisesRegex(RuntimeError, "between 1 and 100"):
                find_issues.main()


class ClaimIssueTests(unittest.TestCase):
    def ready_issue(self):
        return {"state": "OPEN", "labels": [{"name": "status:ready"}]}

    def common(self):
        return [
            patch.object(claim_issue, "get_login", return_value="bot"),
            patch.object(claim_issue, "get_default_branch", return_value="main"),
            patch.object(claim_issue, "get_branch_head", return_value="a" * 40),
        ]

    def test_closed_issue_is_never_claimed(self):
        with patch.object(claim_issue, "read_issue", return_value={"state": "CLOSED", "labels": [{"name": "status:ready"}]}), patch.object(
            claim_issue, "get_login", return_value="bot"
        ), patch.object(sys, "argv", ["claim", "--repo", "o/r", "--issue", "7"]), patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            self.assertEqual(claim_issue.main(), 11)

    def test_non_ready_issue_is_never_claimed(self):
        with patch.object(claim_issue, "read_issue", return_value={"state": "OPEN", "labels": [{"name": "status:blocked"}]}), patch.object(
            claim_issue, "get_login", return_value="bot"
        ), patch.object(sys, "argv", ["claim", "--repo", "o/r", "--issue", "7"]), patch(
            "sys.stdout", new_callable=io.StringIO
        ):
            self.assertEqual(claim_issue.main(), 13)

    def test_existing_claim_branch_loses_race(self):
        def fake_gh(*args, **kwargs):
            if "POST" in args:
                return cp(1, err="exists")
            return cp()

        patches = self.common()
        for p in patches:
            p.start()
        try:
            with patch.object(claim_issue, "read_issue", return_value=self.ready_issue()), patch.object(
                claim_issue, "gh", side_effect=fake_gh
            ), patch.object(claim_issue, "branch_exists", return_value=True), patch.object(
                sys, "argv", ["claim", "--repo", "o/r", "--issue", "7"]
            ), patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(claim_issue.main(), 10)
        finally:
            for p in patches:
                p.stop()

    def test_status_failure_rolls_back_new_claim_branch(self):
        patches = self.common()
        for p in patches:
            p.start()
        try:
            with patch.object(claim_issue, "read_issue", return_value=self.ready_issue()), patch.object(
                claim_issue, "gh", return_value=cp()
            ), patch.object(claim_issue, "set_status", side_effect=RuntimeError("label fail")), patch.object(
                claim_issue, "delete_branch"
            ) as delete, patch.object(sys, "argv", ["claim", "--repo", "o/r", "--issue", "7"]):
                with self.assertRaisesRegex(RuntimeError, "label fail"):
                    claim_issue.main()
                delete.assert_called_once_with("o/r", "codex/issue-7")
        finally:
            for p in patches:
                p.stop()

    def test_success_claims_exact_default_head_and_sets_status(self):
        calls = []

        def fake_gh(*args, **kwargs):
            calls.append(args)
            return cp()

        patches = self.common()
        for p in patches:
            p.start()
        try:
            with patch.object(claim_issue, "read_issue", return_value=self.ready_issue()), patch.object(
                claim_issue, "gh", side_effect=fake_gh
            ), patch.object(claim_issue, "set_status") as status, patch.object(
                sys, "argv", ["claim", "--repo", "o/r", "--issue", "7"]
            ), patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(claim_issue.main(), 0)
            status.assert_called_once_with("o/r", 7, "status:ready", "status:in-progress")
            create = next(c for c in calls if "POST" in c)
            self.assertIn("sha=" + "a" * 40, create)
            self.assertTrue(json.loads(out.getvalue())["claimed"])
        finally:
            for p in patches:
                p.stop()


class WorktreeTests(unittest.TestCase):
    def test_parse_worktrees_preserves_branch_mapping(self):
        text = "worktree /repo\nHEAD aaa\nbranch refs/heads/main\n\nworktree /tmp/r\nHEAD bbb\nbranch refs/heads/codex/issue-7\n\n"
        with patch.object(create_worktree, "git", return_value=cp(out=text)):
            entries = create_worktree.parse_worktrees(Path("/repo"))
        self.assertEqual(entries[1]["branch"], "refs/heads/codex/issue-7")
        self.assertEqual(entries[1]["worktree"], "/tmp/r")

    def test_refuses_issue_branch_in_shared_checkout(self):
        root = Path("/repo").resolve()
        with patch.object(create_worktree, "repo_root", return_value=root), patch.object(
            create_worktree, "git", return_value=cp()
        ), patch.object(create_worktree, "rev_parse", return_value="a" * 40), patch.object(
            create_worktree, "parse_worktrees", return_value=[{"worktree": str(root), "branch": "refs/heads/codex/issue-7"}]
        ), patch.object(sys, "argv", ["worktree", "--issue", "7"]):
            with self.assertRaisesRegex(RuntimeError, "current/shared checkout"):
                create_worktree.main()

    def test_reuses_registered_exact_head_worktree(self):
        root = Path("/repo").resolve()
        wt = Path("/tmp/wt").resolve()

        def rev(path, ref):
            return "a" * 40

        with patch.object(create_worktree, "repo_root", return_value=root), patch.object(
            create_worktree, "git", return_value=cp()
        ), patch.object(create_worktree, "rev_parse", side_effect=rev), patch.object(
            create_worktree, "parse_worktrees", return_value=[{"worktree": str(wt), "branch": "refs/heads/codex/issue-7"}]
        ), patch.object(sys, "argv", ["worktree", "--issue", "7"]), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as out:
            self.assertEqual(create_worktree.main(), 0)
        self.assertTrue(json.loads(out.getvalue())["reused"])

    def test_refuses_existing_unregistered_destination(self):
        root = Path("/repo").resolve()
        with tempfile.TemporaryDirectory() as td:
            target = Path(td)
            with patch.object(create_worktree, "repo_root", return_value=root), patch.object(
                create_worktree, "git", return_value=cp()
            ), patch.object(create_worktree, "rev_parse", return_value="a" * 40), patch.object(
                create_worktree, "parse_worktrees", return_value=[]
            ), patch.object(sys, "argv", ["worktree", "--issue", "7", "--path", str(target)]):
                with self.assertRaisesRegex(RuntimeError, "refusing to delete or reuse"):
                    create_worktree.main()


class ReleaseIssueTests(unittest.TestCase):
    def common(self):
        return [
            patch.object(release_issue, "get_login", return_value="bot"),
            patch.object(release_issue, "get_default_branch", return_value="main"),
        ]

    def argv(self, *extra):
        return ["release", "--repo", "o/r", "--issue", "7", "--reason", "x", "--next-step", "y", *extra]

    def test_open_pr_prevents_release(self):
        patches = self.common()
        [p.start() for p in patches]
        try:
            with patch.object(release_issue, "gh_json", return_value=[{"number": 9}]), patch.object(
                sys, "argv", self.argv()
            ), patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(release_issue.main(), 20)
        finally:
            [p.stop() for p in patches]

    def test_unpreserved_branch_commits_prevent_release(self):
        patches = self.common()
        [p.start() for p in patches]
        try:
            with patch.object(release_issue, "gh_json", return_value=[]), patch.object(
                release_issue, "branch_exists", return_value=True
            ), patch.object(release_issue, "gh", return_value=cp(out="2\n")), patch.object(
                sys, "argv", self.argv()
            ), patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(release_issue.main(), 21)
        finally:
            [p.stop() for p in patches]

    def test_delete_failure_restores_in_progress_state(self):
        calls = []

        def fake_gh(*args, **kwargs):
            calls.append(args)
            if "DELETE" in args:
                return cp(1, err="no")
            return cp(out="0\n")

        patches = self.common()
        [p.start() for p in patches]
        try:
            with patch.object(release_issue, "gh_json", return_value=[]), patch.object(
                release_issue, "branch_exists", side_effect=[True, True, True]
            ), patch.object(release_issue, "transition_status"), patch.object(
                release_issue, "gh", side_effect=fake_gh
            ), patch.object(sys, "argv", self.argv()):
                self.assertEqual(release_issue.main(), 1)
            flattened = [" ".join(c) for c in calls]
            self.assertTrue(any("--add-label status:in-progress" in c for c in flattened))
        finally:
            [p.stop() for p in patches]

    def test_success_transitions_before_branch_delete(self):
        order = []

        def transition(*args):
            order.append("transition")

        def fake_gh(*args, **kwargs):
            if "DELETE" in args:
                order.append("delete")
            return cp(out="0\n")

        patches = self.common()
        [p.start() for p in patches]
        try:
            with patch.object(release_issue, "gh_json", return_value=[]), patch.object(
                release_issue, "branch_exists", side_effect=[True, True]
            ), patch.object(release_issue, "transition_status", side_effect=transition), patch.object(
                release_issue, "gh", side_effect=fake_gh
            ), patch.object(sys, "argv", self.argv()), patch(
                "sys.stdout", new_callable=io.StringIO
            ):
                self.assertEqual(release_issue.main(), 0)
            self.assertLess(order.index("transition"), order.index("delete"))
        finally:
            [p.stop() for p in patches]


if __name__ == "__main__":
    unittest.main(verbosity=2)
