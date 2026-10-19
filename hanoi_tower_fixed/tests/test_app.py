"""python -m unittest discover -s tests -v (requires httpx)"""
import os
from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient
import main


class HanoiApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(main.app)

    def test_home_from_another_working_directory(self):
        original = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                os.chdir(temp_dir)
                response = self.client.get("/")
        finally:
            os.chdir(original)
        self.assertEqual(response.status_code, 200)
        self.assertIn("원판의 개수를 입력하십시오", response.text)
        self.assertIn("calculateMoveLocally", response.text)

    def test_config_version(self):
        response = self.client.get("/api/config")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            "max_disks": 10000,
            "max_visual_disks": 1000,
            "version": "2.1-fixed",
        })

    def test_results(self):
        for n in (1, 3, 100, 1000, 10000):
            with self.subTest(n=n):
                response = self.client.get(f"/api/hanoi/{n}")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["total_moves"], str((1 << n) - 1))
        self.assertEqual(len(str((1 << 10000) - 1)), 3011)

    def test_invalid_n(self):
        for n in (0, 10001):
            self.assertEqual(self.client.get(f"/api/hanoi/{n}").status_code, 400)

    def test_move_sequences(self):
        for n in range(1, 9):
            with self.subTest(n=n):
                towers = [list(range(n, 0, -1)), [], []]
                current = 1
                while current < (1 << n):
                    response = self.client.get(
                        f"/api/hanoi/{n}/moves",
                        params={"start":str(current), "limit":50},
                    )
                    self.assertEqual(response.status_code, 200)
                    moves = response.json()["moves"]
                    self.assertGreater(len(moves), 0)
                    for move in moves:
                        disk = towers[move["from"]].pop()
                        self.assertEqual(disk, move["disk"])
                        if towers[move["to"]]:
                            self.assertLess(disk, towers[move["to"]][-1])
                        towers[move["to"]].append(disk)
                    current += len(moves)
                self.assertEqual(towers, [[], [], list(range(n, 0, -1))])


if __name__ == "__main__":
    unittest.main()
