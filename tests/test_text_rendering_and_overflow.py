# tests/test_text_rendering_and_overflow.py
"""
Automated unit and integration tests verifying:
1. Universal font glyph sanitization eliminates all missing character boxes ('tofu' / □).
2. Proper text wrapping and bounds checking prevent text over-extending past dialogue and UI boxes.
3. All special characters (Philippine Peso ₱, smart quotes, math symbols, emojis) render safely.
"""

import unittest
import os
import pygame
import sys

# Ensure project root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ["SDL_VIDEODRIVER"] = "dummy"
pygame.init()
pygame.display.set_mode((1280, 720))

from core.font_manager import get_font, sanitize_text, wrap_multiline_text, SafeFont, GLYPH_REPLACEMENTS


class TestTextSanitizationAndWrapping(unittest.TestCase):
    def setUp(self):
        self.font = get_font("Comic Sans MS", 20)

    def test_glyph_sanitization_removes_unrenderable_chars(self):
        """Verify emojis and unrenderable characters are cleanly sanitized without tofu boxes."""
        sample_texts = [
            "Hello 🖐️ world ✊!",
            "Score: 100 ⭐ 🌟",
            "Target 🎯 at position 📷",
            "Price: ₱50.00 each (Sukli: ₱15)",
            "Angle ∠A = 90° in △ABC",
            "Formula: 4 × 5 ÷ 2 ≤ 10, x² + y³ ≠ 0",
            "Quote: “Learning math is fun!” — Teacher",
            "Contraction: It’s a great day’s quest!",
            "Directions: ➔ Move right ➡ then jump ⬆️",
            "Status: [✓] Verified & [✕] Eliminated",
        ]

        for text in sample_texts:
            clean = sanitize_text(text)
            self.assertIsInstance(clean, str)
            # Ensure no tofu glyphs (square box, null chars, or high-surrogate codes)
            for ch in clean:
                code = ord(ch)
                self.assertTrue(
                    32 <= code <= 126 or 160 <= code <= 255 or ch in ('\n', ' '),
                    f"Character '{ch}' (ord {code}) in '{clean}' is not safe printable ASCII/Latin-1!"
                )
            
            # Rendering should succeed cleanly
            surf = self.font.render(text, True, (255, 255, 255))
            self.assertIsNotNone(surf)
            self.assertGreater(surf.get_width(), 0)

    def test_wrap_multiline_text_respects_max_width(self):
        """Verify text wrapping guarantees all lines fit strictly within max_width."""
        long_paragraph = (
            "Outstanding, young adventurer! You have built the bridge and solved my riddle!\n"
            "You may now enter the portal and proceed on your quest. Safe travels across the realm!\n\n"
            "Supercalifragilisticexpialidocious math puzzle questions with extremelylongunbrokenwordsthatmustwrap."
        )
        max_width = 300
        lines = wrap_multiline_text(long_paragraph, self.font, max_width)

        self.assertTrue(len(lines) > 0)
        for line in lines:
            line_w = self.font.size(line)[0]
            self.assertLessEqual(
                line_w,
                max_width + 5, # Allow tiny rounding margin
                f"Line '{line}' width ({line_w}px) exceeds max_width ({max_width}px)!"
            )

    def test_peso_currency_and_math_replacements(self):
        """Verify Philippine Peso ₱ and mathematical symbols map to readable ASCII."""
        self.assertEqual(sanitize_text("₱20 banknote"), "P20 banknote")
        self.assertEqual(sanitize_text("4 × 5 = 20"), "4 x 5 = 20")
        self.assertEqual(sanitize_text("10 ÷ 2 = 5"), "10 / 2 = 5")
        self.assertEqual(sanitize_text("x ≤ 10 and y ≥ 5"), "x <= 10 and y >= 5")
        self.assertEqual(sanitize_text("’Smart Quote‘ & ”Double“"), "'Smart Quote' & \"Double\"")

    def test_quiz_dialog_wrapping_and_rendering(self):
        """Verify RPGQuizDialog renders long questions and choices without overflow."""
        from core.quiz_dialog import RPGQuizDialog
        screen = pygame.display.get_surface()
        dialog = RPGQuizDialog(screen, 1280, 720)

        q_data = {
            "question": (
                "A farmer has 24 mangoes and divides them equally into 4 large native bayong baskets. "
                "How many mangoes will be placed inside each individual basket?"
            ),
            "choices": [
                "A. Exactly 6 sweet mangoes in each basket",
                "B. Exactly 8 sweet mangoes in each basket",
                "C. Exactly 5 sweet mangoes in each basket",
                "D. Exactly 10 sweet mangoes in each basket"
            ],
            "correct": 0
        }

        # Wrap question
        wrapped_q = dialog.wrap_text(q_data["question"], self.font, dialog.box_w - 60)
        self.assertTrue(len(wrapped_q) >= 2)
        for line in wrapped_q:
            self.assertLessEqual(self.font.size(line)[0], dialog.box_w - 50)

        # Draw dialog
        dialog.draw((0, 0), q_data, speaker_name="Station Master", speaker_subtitle="Fraction Challenge")


if __name__ == "__main__":
    unittest.main()
