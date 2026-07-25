import datetime as dt
import unittest

from scripts.render_heatmap_svg import builder_scene


class CommitBuilderSceneTests(unittest.TestCase):
    def test_upper_weekday_square_gets_a_ladder(self) -> None:
        first_sunday = dt.date(2026, 7, 19)
        days = [{"date": "2026-07-20", "count": 1, "level": 1}]

        _, parts = builder_scene(days, first_sunday, 48, 44, 805)

        self.assertIn('class="builder-ladder"', "\n".join(parts))

    def test_bottom_weekday_square_does_not_need_a_ladder(self) -> None:
        first_sunday = dt.date(2026, 7, 19)
        days = [{"date": "2026-07-25", "count": 1, "level": 1}]

        _, parts = builder_scene(days, first_sunday, 48, 44, 805)

        self.assertNotIn('class="builder-ladder"', "\n".join(parts))

    def test_scene_contains_all_comic_animation_beats(self) -> None:
        first_sunday = dt.date(2026, 7, 19)
        days = [{"date": "2026-07-25", "count": 1, "level": 1}]

        css, parts = builder_scene(days, first_sunday, 48, 44, 805)
        scene = "\n".join(parts)

        self.assertIn("builder-route", css)
        self.assertIn("Building today’s square!", scene)
        self.assertIn("One more commit!", scene)
        self.assertIn("Whoa—hard hat works!", scene)
        self.assertIn("Break time… zzz", scene)


if __name__ == "__main__":
    unittest.main()
