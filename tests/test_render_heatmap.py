import datetime as dt
import unittest

from scripts.render_heatmap_svg import WEEKDAY_STORIES, builder_scene


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

    def test_scene_contains_3d_character_and_props(self) -> None:
        first_sunday = dt.date(2026, 7, 19)
        days = [{"date": "2026-07-25", "count": 1, "level": 1}]

        css, parts = builder_scene(days, first_sunday, 48, 44, 805)
        scene = "\n".join(parts)

        self.assertIn("builder-route", css)
        self.assertIn('id="builder-head"', scene)
        self.assertIn('id="builder-mouth"', scene)
        self.assertIn('class="builder-eye"', scene)
        self.assertIn('id="builder-hat"', scene)
        self.assertIn('id="builder-hammer"', scene)
        self.assertIn('id="target-block"', scene)
        self.assertIn('id="builder-toolbox"', scene)

    def test_every_weekday_has_20_plus_animations_and_eight_lines(self) -> None:
        first_sunday = dt.date(2026, 7, 19)

        for weekday in range(7):
            target_date = first_sunday + dt.timedelta(days=weekday + 1)
            days = [{
                "date": target_date.isoformat(),
                "count": 1,
                "level": 1,
            }]

            css, parts = builder_scene(days, first_sunday, 48, 44, 805)
            scene = "\n".join(parts)
            story = WEEKDAY_STORIES[weekday]

            with self.subTest(weekday=weekday):
                self.assertGreaterEqual(css.count("@keyframes"), 20)
                self.assertEqual(len(story["messages"]), 8)
                self.assertIn(story["shift"], scene)
                for message in story["messages"]:
                    self.assertIn(message, scene)


if __name__ == "__main__":
    unittest.main()
