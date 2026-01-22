import pathlib
import subprocess
import sys
import tempfile
import unittest

repo_root_path = pathlib.Path(__file__).parent.parent


class SystemTest(unittest.TestCase):

    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        subprocess.run(
            ';'.join(
                [
                    'cd "{}"'.format(self.tempdir.name),
                    '{} -m venv ./venv'.format(sys.executable),
                    './venv/bin/python -m pip install "{}" -qq'.format(repo_root_path),
                ]
            ),
            shell=True,
            check=True,
            stdout=subprocess.PIPE,
        )

    def tearDown(self):
        self.tempdir.cleanup()

    def test(self):
        result = subprocess.run(
            ';'.join(
                [
                    'cd "{}"'.format(self.tempdir.name),
                    'git clone https://github.com/BMCV/galaxy-image-analysis.git',
                    './venv/bin/python -m gialint --tool_path galaxy-image-analysis/tools',
                ]
            ),
            shell=True,
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if 'traceback' in result.stderr.lower():
            print('\n', result.stderr, file=sys.stderr)
            self.fail()
