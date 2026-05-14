import unittest
from pathlib import Path


class TestRepoAssets(unittest.TestCase):
    def setUp(self):
        self.repo_root = Path(__file__).resolve().parents[1]

    def test_ui_html_exists(self):
        self.assertTrue((self.repo_root / "ui.html").is_file())

    def test_schedule_files_exist(self):
        self.assertTrue((self.repo_root / "alarm_data.txt").is_file())
        self.assertTrue((self.repo_root / "schedule.txt").is_file())
