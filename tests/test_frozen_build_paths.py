# tests/test_frozen_build_paths.py - Verifies asset and path resolution for frozen builds
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.paths import get_base_dir, get_asset_path, get_db_path, get_dataset_path, resolve_path
from screens.map_loader import MapLoader


class TestFrozenBuildPaths(unittest.TestCase):
    def setUp(self):
        self.original_base_dir = get_base_dir()

    def test_dev_environment_base_dir(self):
        """In normal development mode, get_base_dir resolves to repository root."""
        base_dir = get_base_dir()
        self.assertTrue(os.path.isdir(os.path.join(base_dir, "assets")))
        self.assertTrue(os.path.isdir(os.path.join(base_dir, "db")))
        self.assertTrue(os.path.isdir(os.path.join(base_dir, "datasets")))

    def test_frozen_simulation_app_dir(self):
        """Simulating PyInstaller sys.frozen = True resolves base_dir to sys.executable directory."""
        fake_exe = os.path.join(self.original_base_dir, "dist", "CognitiveMaze", "CognitiveMaze.exe")
        with patch.object(sys, "frozen", True, create=True), \
             patch.object(sys, "executable", fake_exe), \
             patch("core.paths._BASE_DIR", None):

            # If dist/CognitiveMaze has assets, it will resolve to dist/CognitiveMaze
            if os.path.isdir(os.path.join(self.original_base_dir, "dist", "CognitiveMaze", "assets")):
                resolved = get_base_dir()
                expected = os.path.abspath(os.path.join(self.original_base_dir, "dist", "CognitiveMaze"))
                self.assertEqual(os.path.abspath(resolved), expected)

    def test_essential_assets_exist_and_resolve(self):
        """Validates that key game assets resolve to existing files on disk."""
        essential_files = [
            get_asset_path("map", "map.txt"),
            get_asset_path("map", "Quarter1Maps", "map1.txt"),
            get_asset_path("map", "tutorial_map.txt"),
            get_asset_path("images", "menu_background.png"),
            get_asset_path("images", "boy.png"),
            get_asset_path("images", "girl.png"),
            get_asset_path("images", "icon.ico"),
            get_asset_path("fonts", "Pixelfont.otf"),
            get_asset_path("sounds", "backgroundgamesoundloop.wav"),
            get_asset_path("models", "hand_landmarker.task"),
        ]

        for file_path in essential_files:
            self.assertTrue(os.path.exists(file_path), f"Essential asset missing: {file_path}")

    def test_resolve_path_helper(self):
        """Verifies resolve_path handles bare, relative, and assets/ prefixed paths."""
        resolved = resolve_path("assets/fonts/Pixelfont.otf")
        self.assertTrue(os.path.exists(resolved))

        resolved2 = resolve_path("fonts/Pixelfont.otf")
        self.assertTrue(os.path.exists(resolved2))

        resolved3 = resolve_path(get_asset_path("fonts", "Pixelfont.otf"))
        self.assertTrue(os.path.exists(resolved3))

    def test_map_loader_resolution(self):
        """Verifies MapLoader correctly locates and parses maps using get_base_dir()."""
        loader = MapLoader()
        self.assertTrue(loader.load_map("map.txt"))
        self.assertGreater(loader.rows, 0)
        self.assertGreater(loader.cols, 0)

        self.assertTrue(loader.load_map("map1.txt"))
        self.assertGreater(loader.rows, 0)
        self.assertGreater(loader.cols, 0)


if __name__ == "__main__":
    unittest.main()

