
import re


def analyze_complaint(text):

    text = str(text).lower()

    # --------------------------------
    # CATEGORY PREDICTION
    # --------------------------------

    categories = {
        "Electrical": [
            "electricity", "power cut", "light",
            "fan", "switch", "wiring", "socket",
            "electric shock", "short circuit"
        ],

        "Water": [
            "water", "tap", "pipeline", "leakage",
            "drinking water", "water supply"
        ],

        "Cleanliness": [
            "garbage", "dustbin", "dirty", "cleaning",
            "toilet", "washroom", "sanitation",
            "bad smell", "waste"
        ],

        "Infrastructure": [
            "classroom", "building", "bench",
            "desk", "door", "window", "roof",
            "broken", "damaged", "furniture"
        ],

        "Network": [
            "wifi", "internet", "network",
            "connection", "computer", "server"
        ],

        "Safety": [
            "fire", "accident", "security",
            "theft", "harassment", "emergency",
            "danger", "unsafe", "injury"
        ],

        "Academic": [
            "teacher", "faculty", "class",
            "timetable", "exam", "lecture",
            "attendance", "laboratory"
        ]
    }

    category = "General"

    for category_name, keywords in categories.items():

        if any(keyword in text for keyword in keywords):
            category = category_name
            break

    # --------------------------------
    # PRIORITY PREDICTION
    # --------------------------------

    high_priority = [
        "fire", "electric shock", "short circuit",
        "accident", "emergency", "injury",
        "serious injury", "harassment",
        "theft", "danger", "unsafe",
        "gas leak", "building collapse",
        "water flooding"
    ]

    low_priority = [
        "suggestion", "minor issue",
        "small issue", "cosmetic",
        "decoration", "feedback",
        "improvement", "not urgent",
        "minor cleaning"
    ]

    medium_priority = [
        "not working", "broken", "damaged",
        "repair", "leakage", "no water",
        "no internet", "wifi problem",
        "fan not working", "light not working",
        "projector", "computer problem",
        "maintenance", "cleaning"
    ]

    # Check HIGH first because safety issues need attention.
    if any(keyword in text for keyword in high_priority):
        priority = "High"

    elif any(keyword in text for keyword in low_priority):
        priority = "Low"

    elif any(keyword in text for keyword in medium_priority):
        priority = "Medium"

    else:
        # Default priority for an ordinary complaint
        priority = "Medium"

    return category, priority
