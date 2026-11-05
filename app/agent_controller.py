# ============================================================
# AGENT CONTROLLER
# ============================================================

MAX_RETRIES = 2


def decide_next_action(
    verification_result,
    retry_count=0,
):
    """
    Decide the next action using verification and generation status.

    Supported decisions:
        ACCEPT
        RETRIEVE_AGAIN
        REGENERATE
        INSUFFICIENT_EVIDENCE
    """

    # Stop immediately when the generator's evidence gate
    # explicitly identifies missing historical evidence.
    stop_reason = verification_result.get("stop_reason")

    if stop_reason == "EVIDENCE_GATE_REJECTED":
        return "INSUFFICIENT_EVIDENCE"

    verification = verification_result.get(
        "verification",
        "UNSUPPORTED",
    )

    if verification == "SUPPORTED":
        return "ACCEPT"

    if retry_count >= MAX_RETRIES:
        return "INSUFFICIENT_EVIDENCE"

    if verification == "UNSUPPORTED":
        return "RETRIEVE_AGAIN"

    return "INSUFFICIENT_EVIDENCE"


if __name__ == "__main__":

    test_cases = [
        (
            "Supported answer",
            {"verification": "SUPPORTED"},
            0,
            "ACCEPT",
        ),
        (
            "Ordinary unsupported answer",
            {"verification": "UNSUPPORTED"},
            0,
            "RETRIEVE_AGAIN",
        ),
        (
            "Historical evidence gate rejected",
            {
                "verification": "UNSUPPORTED",
                "stop_reason": "EVIDENCE_GATE_REJECTED",
            },
            0,
            "INSUFFICIENT_EVIDENCE",
        ),
        (
            "Retry limit reached",
            {"verification": "UNSUPPORTED"},
            2,
            "INSUFFICIENT_EVIDENCE",
        ),
    ]

    print("=" * 60)
    print("AGENT CONTROLLER TEST")
    print("=" * 60)

    for name, result, retry_count, expected in test_cases:
        actual = decide_next_action(result, retry_count)

        status = "PASS" if actual == expected else "FAIL"

        print(f"\n{name}")
        print(f"Expected: {expected}")
        print(f"Actual:   {actual}")
        print(f"Result:   {status}")
