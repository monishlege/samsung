import re


CATEGORY_KEYWORDS = {
    "Safety": [
        "fire", "smoke", "electric shock", "accident", "security",
        "theft", "harassment", "emergency", "danger", "unsafe",
        "injury", "injured", "assault", "gas leak", "building collapse",
    ],
    "Electrical": [
        "electricity", "power cut", "light", "fan", "switch", "wiring",
        "socket", "short circuit",
    ],
    "Water": [
        "water", "tap", "pipeline", "leakage", "drinking water",
        "water supply",
    ],
    "Cleanliness": [
        "garbage", "dustbin", "dirty", "cleaning", "toilet", "washroom",
        "sanitation", "bad smell", "waste",
    ],
    "Infrastructure": [
        "classroom", "building", "bench", "desk", "door", "window",
        "roof", "broken", "damaged", "furniture",
    ],
    "Network": [
        "wifi", "internet", "network", "connection", "computer", "server",
    ],
    "Academic": [
        "teacher", "faculty", "class", "timetable", "exam", "lecture",
        "attendance", "laboratory",
    ],
}

HIGH_PRIORITY_KEYWORDS = [
    "fire", "smoke", "electric shock", "live wire", "short circuit",
    "gas leak", "explosion", "accident", "emergency", "injury", "injured",
    "bleeding", "unconscious", "harassment", "assault", "threat",
    "unsafe", "danger", "flooding", "collapse", "collapsing",
    "falling ceiling",
]

MEDIUM_PRIORITY_KEYWORDS = [
    "not working", "isn't working", "doesn't work", "broken", "damaged",
    "repair", "leak", "leakage", "no water", "no electricity", "no power",
    "no internet", "no wifi", "wifi problem", "maintenance",
]

LOW_PRIORITY_KEYWORDS = [
    "suggestion", "minor issue", "small issue", "cosmetic", "decoration",
    "feedback", "improvement", "not urgent", "minor cleaning",
]

NEGATION_WORDS = {"no", "not", "never", "without", "absent", "neither"}

RESOLUTION_CONFIRMED_TERMS = [
    "fixed", "repaired", "resolved", "restored", "completed",
    "working now", "works now", "working again", "functioning normally",
    "operational now", "cleaned", "unclogged", "reconnected", "sealed",
    "replaced and tested",
]

RESOLUTION_OPEN_TERMS = [
    "not fixed", "not repaired", "not resolved", "not completed",
    "still broken", "still leaking", "still not working", "issue remains",
    "problem remains", "needs repair", "pending repair", "awaiting parts",
    "unable to repair", "could not repair", "couldn't repair",
    "cannot repair", "still needs work",
]


def _normalize_text(text):
    return re.sub(r"[\W_]+", " ", str(text).lower()).strip()


def _has_term(text, term):
    return re.search(rf"\b{re.escape(term)}\b", text) is not None


def _has_unnegated_term(text, terms):
    for term in terms:
        for match in re.finditer(rf"\b{re.escape(term)}\b", text):
            preceding_words = re.findall(
                r"\b\w+\b",
                text[max(0, match.start() - 48):match.start()],
            )
            for contrast in ("but", "however", "yet", "except"):
                if contrast in preceding_words:
                    preceding_words = preceding_words[
                        preceding_words.index(contrast) + 1:
                    ]
            if not NEGATION_WORDS.intersection(preceding_words[-4:]):
                return True
    return False


def analyze_complaint(text):
    normalized_text = _normalize_text(text)

    category = "General"
    for category_name, keywords in CATEGORY_KEYWORDS.items():
        if any(_has_term(normalized_text, keyword) for keyword in keywords):
            category = category_name
            break

    if _has_unnegated_term(normalized_text, HIGH_PRIORITY_KEYWORDS):
        priority = "High"
    elif any(
        _has_term(normalized_text, keyword)
        for keyword in MEDIUM_PRIORITY_KEYWORDS
    ):
        priority = "Medium"
    elif any(
        _has_term(normalized_text, keyword)
        for keyword in LOW_PRIORITY_KEYWORDS
    ):
        priority = "Low"
    else:
        priority = "Medium"

    return category, priority


def review_resolution(resolution_notes):
    normalized_notes = _normalize_text(resolution_notes)
    if not normalized_notes:
        return False, "Add notes describing the work performed and its outcome."

    if any(_has_term(normalized_notes, term) for term in RESOLUTION_OPEN_TERMS):
        return (
            False,
            "The notes indicate that work may still be needed. "
            "The complaint remains open.",
        )

    if any(
        _has_term(normalized_notes, term)
        for term in RESOLUTION_CONFIRMED_TERMS
    ):
        return (
            True,
            "The notes state that the issue was fixed, restored, completed, "
            "or is working.",
        )

    return (
        False,
        "The notes do not clearly confirm the issue is fixed. "
        "Describe the repair and its result.",
    )
