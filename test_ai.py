import unittest

from ai_engine import analyze_complaint


class ComplaintAnalysisTests(unittest.TestCase):
    def test_safety_emergencies_are_high_priority(self):
        self.assertEqual(
            analyze_complaint("There is a fire in the computer lab"),
            ("Safety", "High"),
        )
        self.assertEqual(
            analyze_complaint("The roof is collapsing and someone is injured"),
            ("Safety", "High"),
        )

    def test_routine_repairs_are_medium_priority(self):
        self.assertEqual(
            analyze_complaint("The classroom fan is not working"),
            ("Electrical", "Medium"),
        )
        self.assertEqual(
            analyze_complaint("The campus wifi is not working"),
            ("Network", "Medium"),
        )
        self.assertEqual(
            analyze_complaint(
                "The fan is not working but this is not urgent"
            )[1],
            "Medium",
        )

    def test_minor_feedback_is_low_priority(self):
        self.assertEqual(
            analyze_complaint("I have a suggestion to improve the library")[1],
            "Low",
        )
        self.assertEqual(
            analyze_complaint("The washroom needs minor cleaning")[1],
            "Low",
        )

    def test_negated_emergency_does_not_escalate(self):
        self.assertEqual(
            analyze_complaint("There is no fire or danger; this is a suggestion")[1],
            "Low",
        )
        self.assertEqual(
            analyze_complaint(
                "There is no fire, but an electric shock near the switch"
            )[1],
            "High",
        )


if __name__ == "__main__":
    unittest.main()
