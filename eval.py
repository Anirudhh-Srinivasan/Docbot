"""Small manual retrieval-and-answer smoke evaluation against a running DocBot."""

import requests

BASE_URL = "http://127.0.0.1:8000"
CASES = [
    ("How long does a workspace invitation last?", ["7 days"]),
    ("What is Orbit Team pricing per member each month?", ["$12", "member"]),
    ("How much does annual billing discount paid plans?", ["15%"]),
    ("What permission does the GitHub integration need to sync issues?", ["Issues"]),
    ("What is the Orbit API rate limit per token?", ["120", "minute"]),
    ("How long are encrypted backups retained?", ["30 days"]),
]


def main() -> None:
    passed = 0
    for question, expected_keywords in CASES:
        try:
            response = requests.post(f"{BASE_URL}/ask", json={"question": question}, timeout=90)
            response.raise_for_status()
            answer = response.json()["answer"].lower()
            matched = [keyword for keyword in expected_keywords if keyword.lower() in answer]
            passed_case = len(matched) == len(expected_keywords)
            message = "PASS" if passed_case else f"FAIL (found {matched})"
        except requests.RequestException as exc:
            passed_case, message = False, f"ERROR ({exc})"
        except (KeyError, ValueError) as exc:
            passed_case, message = False, f"ERROR (unexpected response: {exc})"
        passed += int(passed_case)
        print(f"[{message}] {question}")
    print(f"\nScore: {passed}/{len(CASES)}")


if __name__ == "__main__":
    main()
