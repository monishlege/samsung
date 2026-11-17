
from ai_engine import analyze_complaint

test_complaints = [
    "There is a fire in the computer lab",
    "The classroom fan is not working",
    "I have a suggestion to improve the library",
    "There is an electric shock near the switch",
    "The washroom needs minor cleaning",
    "The campus wifi is not working"
]

for complaint in test_complaints:

    category, priority = analyze_complaint(complaint)

    print("Complaint:", complaint)
    print("Category:", category)
    print("Priority:", priority)
    print("-" * 40)
