import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class FlatpakManifestTests(unittest.TestCase):
    def test_runtime_design_tokens_are_installed_at_the_path_used_by_ui(self):
        manifest = json.loads(
            (ROOT / 'packaging/flatpak/io.github.obaidr1.obiview.json').read_text()
        )
        module = next(item for item in manifest['modules'] if item['name'] == 'bildblick')
        command = next(
            line for line in module['build-commands']
            if 'design-system/tokens.json' in line
        )

        with tempfile.TemporaryDirectory() as temporary:
            environment = os.environ | {'FLATPAK_DEST': temporary}
            subprocess.run(command, cwd=ROOT, env=environment, shell=True, check=True)
            installed = Path(temporary) / 'share/bildblick/design-system/tokens.json'
            self.assertTrue(installed.is_file())
            json.loads(installed.read_text())


if __name__ == '__main__':
    unittest.main()
