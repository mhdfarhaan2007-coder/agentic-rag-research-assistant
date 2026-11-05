import re


# ============================================================
# CONFIGURATION
# ============================================================

# Minimum amount of claim content that should appear
# in the evidence for normal factual claims.
MIN_WORD_COVERAGE = 0.50


# Historical claims are treated more strictly.
# The evidence must explicitly contain a historical
# relationship instead of merely mentioning the same people/topic.
HISTORICAL_PATTERNS = [
    "invented",
    "introduced",
    "developed",
    "created",
    "founded",
    "discovered",
    "originated",
    "first developed",
    "first introduced",
    "pioneered",
]


RELATIONSHIP_PATTERNS = [
    "subset of",
    "part of",
    "branch of",
    "type of",
    "form of",
    "category of",
]


STOP_WORDS = {
    "a",
    "an",
    "the",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "and",
    "or",
    "but",
    "of",
    "to",
    "in",
    "on",
    "for",
    "from",
    "with",
    "by",
    "as",
    "at",
    "it",
    "this",
    "that",
    "these",
    "those",
    "they",
    "them",
    "their",
    "its",
    "can",
    "may",
    "could",
    "would",
    "should",
    "will",
    "has",
    "have",
    "had",
    "do",
    "does",
    "did",
}


# ============================================================
# TEXT NORMALIZATION
# ============================================================

def normalize_text(text: str) -> str:
    """
    Normalize text for deterministic comparison.
    """

    text = text.lower()

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CONTENT WORD EXTRACTION
# ============================================================

def extract_content_words(text: str) -> list[str]:
    """
    Extract meaningful words while ignoring common stop words.
    """

    words = re.findall(
        r"\b[a-zA-Z][a-zA-Z0-9-]*\b",
        text.lower()
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS
        and len(word) > 2
    ]


# ============================================================
# WORD COVERAGE
# ============================================================

def calculate_word_coverage(
    claim: str,
    evidence: str
) -> float:
    """
    Calculate how much of the claim's important vocabulary
    appears in the evidence.
    """

    claim_words = set(
        extract_content_words(claim)
    )

    evidence_words = set(
        extract_content_words(evidence)
    )

    if not claim_words:
        return 0.0

    matched_words = claim_words.intersection(
        evidence_words
    )

    return len(matched_words) / len(claim_words)


# ============================================================
# NUMBER CHECK
# ============================================================

def extract_numbers(text: str) -> list[str]:
    return re.findall(
        r"\b\d+(?:\.\d+)?\b",
        text
    )


def check_numbers(
    claim: str,
    evidence: str
) -> bool:
    """
    Every number appearing in the claim must also appear
    in the evidence.
    """

    claim_numbers = extract_numbers(claim)
    evidence_numbers = extract_numbers(evidence)

    if not claim_numbers:
        return True

    for number in claim_numbers:
        if number not in evidence_numbers:
            return False

    return True


# ============================================================
# YEAR CHECK
# ============================================================

def extract_years(text: str) -> list[str]:
    return re.findall(
        r"\b(?:1[5-9]\d{2}|20\d{2}|21\d{2})\b",
        text
    )


def check_years(
    claim: str,
    evidence: str
) -> bool:
    """
    Every year appearing in the claim must also appear
    in the evidence.
    """

    claim_years = extract_years(claim)
    evidence_years = extract_years(evidence)

    if not claim_years:
        return True

    for year in claim_years:
        if year not in evidence_years:
            return False

    return True


# ============================================================
# HISTORICAL CLAIM DETECTION
# ============================================================

def get_historical_patterns(
    claim: str
) -> list[str]:
    """
    Return historical words/phrases present in the claim.
    """

    claim_lower = normalize_text(claim)

    found = []

    for pattern in HISTORICAL_PATTERNS:

        if pattern in claim_lower:
            found.append(pattern)

    return found


# ============================================================
# RELATIONSHIP CLAIM DETECTION
# ============================================================

def get_relationship_patterns(
    claim: str
) -> list[str]:
    """
    Return relationship phrases present in the claim.
    """

    claim_lower = normalize_text(claim)

    found = []

    for pattern in RELATIONSHIP_PATTERNS:

        if pattern in claim_lower:
            found.append(pattern)

    return found


# ============================================================
# SUBJECT / ENTITY CHECK
# ============================================================

def extract_capitalized_entities(
    claim: str
) -> list[str]:
    """
    Extract simple named entities from a claim.

    Example:

    Sutton and Barto introduced reinforcement learning.

    -> Sutton
    -> Barto
    """

    entities = re.findall(
        r"\b[A-Z][a-zA-Z-]{2,}\b",
        claim
    )

    ignored = {
        "The",
        "This",
        "That",
        "Machine",
        "Learning",
        "Deep",
        "Artificial",
        "Intelligence",
        "Natural",
        "Language",
        "Processing",
        "Reinforcement",
    }

    return [
        entity
        for entity in entities
        if entity not in ignored
    ]


def check_entities(
    claim: str,
    evidence: str
) -> bool:
    """
    Make sure important named entities in the claim
    occur in the evidence.
    """

    entities = extract_capitalized_entities(
        claim
    )

    evidence_lower = normalize_text(
        evidence
    )

    for entity in entities:

        if normalize_text(entity) not in evidence_lower:
            return False

    return True


# ============================================================
# HISTORICAL CLAIM CHECK
# ============================================================

def check_historical_claim(
    claim: str,
    evidence: str
) -> tuple[bool, str]:
    """
    Historical claims require explicit historical language
    in the evidence.

    Example:

    CLAIM:
    Sutton and Barto introduced reinforcement learning.

    EVIDENCE:
    Sutton & Barto (1998). Reinforcement learning:
    An introduction.

    Result:
    UNSUPPORTED

    because the evidence does not explicitly say
    that they introduced it.
    """

    patterns = get_historical_patterns(
        claim
    )

    if not patterns:
        return True, ""

    evidence_lower = normalize_text(
        evidence
    )

    # --------------------------------------------------------
    # Historical wording must exist in the evidence.
    # --------------------------------------------------------

    matched_historical_word = False

    for pattern in patterns:

        if pattern in evidence_lower:
            matched_historical_word = True
            break

    if not matched_historical_word:

        return (
            False,
            "Historical claim is not explicitly stated in the evidence."
        )

    # --------------------------------------------------------
    # Important named entities must also occur.
    # --------------------------------------------------------

    if not check_entities(
        claim,
        evidence
    ):

        return (
            False,
            "Important entity from the historical claim is missing from the evidence."
        )

    return True, ""


# ============================================================
# RELATIONSHIP CLAIM CHECK
# ============================================================

def check_relationship_claim(
    claim: str,
    evidence: str
) -> tuple[bool, str]:
    """
    Relationship claims such as:

    Deep learning is a subset of machine learning.

    require the relationship to be explicitly present.
    """

    patterns = get_relationship_patterns(
        claim
    )

    if not patterns:
        return True, ""

    claim_lower = normalize_text(
        claim
    )

    evidence_lower = normalize_text(
        evidence
    )

    for pattern in patterns:

        if pattern in claim_lower:

            if pattern not in evidence_lower:

                return (
                    False,
                    f"The relationship '{pattern}' is not explicitly present in the evidence."
                )

    return True, ""


# ============================================================
# CLAIM VS ONE EVIDENCE CHUNK
# ============================================================

def verify_claim_against_chunk(
    claim: str,
    chunk: dict
) -> dict:
    """
    Verify one claim against one retrieved chunk.

    This verifier is intentionally conservative.
    """

    evidence = chunk.get(
        "text",
        ""
    )

    if not evidence.strip():

        return {
            "verification": "UNSUPPORTED",
            "similarity": 0.0,
            "word_coverage": 0.0,
            "reason": "Evidence chunk is empty."
        }

    claim_normalized = normalize_text(
        claim
    )

    evidence_normalized = normalize_text(
        evidence
    )

    # --------------------------------------------------------
    # Exact sentence / phrase match
    # --------------------------------------------------------

    if claim_normalized in evidence_normalized:

        return {
            "verification": "SUPPORTED",
            "similarity": 1.0,
            "word_coverage": 1.0,
            "reason": "Claim appears directly in the evidence."
        }

    # --------------------------------------------------------
    # Number consistency
    # --------------------------------------------------------

    if not check_numbers(
        claim,
        evidence
    ):

        return {
            "verification": "UNSUPPORTED",
            "similarity": 0.0,
            "word_coverage": 0.0,
            "reason": (
                "A number in the claim is not present "
                "in the evidence."
            )
        }

    # --------------------------------------------------------
    # Year consistency
    # --------------------------------------------------------

    if not check_years(
        claim,
        evidence
    ):

        return {
            "verification": "UNSUPPORTED",
            "similarity": 0.0,
            "word_coverage": 0.0,
            "reason": (
                "A year in the claim is not present "
                "in the evidence."
            )
        }

    # --------------------------------------------------------
    # Entity consistency
    # --------------------------------------------------------

    if not check_entities(
        claim,
        evidence
    ):

        return {
            "verification": "UNSUPPORTED",
            "similarity": 0.0,
            "word_coverage": 0.0,
            "reason": (
                "An important named entity in the claim "
                "is missing from the evidence."
            )
        }

    # --------------------------------------------------------
    # Historical claim check
    # --------------------------------------------------------

    historical_ok, historical_reason = (
        check_historical_claim(
            claim,
            evidence
        )
    )

    if not historical_ok:

        return {
            "verification": "UNSUPPORTED",
            "similarity": 0.0,
            "word_coverage": calculate_word_coverage(
                claim,
                evidence
            ),
            "reason": historical_reason
        }

    # --------------------------------------------------------
    # Relationship claim check
    # --------------------------------------------------------

    relationship_ok, relationship_reason = (
        check_relationship_claim(
            claim,
            evidence
        )
    )

    if not relationship_ok:

        return {
            "verification": "UNSUPPORTED",
            "similarity": 0.0,
            "word_coverage": calculate_word_coverage(
                claim,
                evidence
            ),
            "reason": relationship_reason
        }

    # --------------------------------------------------------
    # Lexical coverage
    # --------------------------------------------------------

    word_coverage = calculate_word_coverage(
        claim,
        evidence
    )

    # --------------------------------------------------------
    # Support decision
    # --------------------------------------------------------

    if word_coverage >= MIN_WORD_COVERAGE:

        return {
            "verification": "SUPPORTED",
            "similarity": word_coverage,
            "word_coverage": word_coverage,
            "reason": (
                "The evidence contains sufficient "
                "claim-specific factual content."
            )
        }

    # --------------------------------------------------------
    # Not enough evidence
    # --------------------------------------------------------

    return {
        "verification": "UNSUPPORTED",
        "similarity": word_coverage,
        "word_coverage": word_coverage,
        "reason": (
            "The evidence is related to the claim but "
            "does not contain enough claim-specific information."
        )
    }


# ============================================================
# VERIFY ONE CLAIM AGAINST ALL RETRIEVED CHUNKS
# ============================================================

def verify_claim(
    claim: str,
    retrieved_chunks: list[dict]
) -> dict:
    """
    Verify a single claim against all retrieved chunks.
    """

    supporting_evidence = []

    best_score = 0.0
    best_word_coverage = 0.0
    best_reason = ""

    for chunk in retrieved_chunks:

        result = verify_claim_against_chunk(
            claim,
            chunk
        )

        score = result.get(
            "similarity",
            0.0
        )

        word_coverage = result.get(
            "word_coverage",
            0.0
        )

        # Track strongest evidence candidate.
        if score > best_score:

            best_score = score
            best_word_coverage = word_coverage
            best_reason = result.get(
                "reason",
                ""
            )

        # ----------------------------------------------------
        # ONLY add genuinely supported evidence.
        # ----------------------------------------------------

        if result["verification"] == "SUPPORTED":

            supporting_evidence.append({

                "document_id":
                    chunk.get(
                        "document_id"
                    ),

                "document_name":
                    chunk.get(
                        "document_name"
                    ),

                "chunk_id":
                    chunk.get(
                        "chunk_id"
                    ),

                "similarity":
                    round(
                        score,
                        4
                    ),

                "word_coverage":
                    round(
                        word_coverage,
                        4
                    ),
            })

    # --------------------------------------------------------
    # CLAIM SUPPORTED
    # --------------------------------------------------------

    if supporting_evidence:

        return {

            "claim":
                claim,

            "verification":
                "SUPPORTED",

            "supporting_evidence":
                supporting_evidence,

            "best_similarity":
                round(
                    best_score,
                    4
                ),

            "best_word_coverage":
                round(
                    best_word_coverage,
                    4
                ),

            "reason":
                "At least one evidence chunk directly supports the claim."
        }

    # --------------------------------------------------------
    # CLAIM UNSUPPORTED
    # --------------------------------------------------------

    return {

        "claim":
            claim,

        "verification":
            "UNSUPPORTED",

        "supporting_evidence":
            [],

        "best_similarity":
            round(
                best_score,
                4
            ),

        "best_word_coverage":
            round(
                best_word_coverage,
                4
            ),

        "reason":
            best_reason
            or "No retrieved evidence directly supports the claim."
    }


# ============================================================
# VERIFY COMPLETE ANSWER
# ============================================================

def verify_answer(
    claims: list[str],
    retrieved_chunks: list[dict]
) -> dict:
    """
    Verify every factual claim in the generated answer.

    Overall answer is SUPPORTED only when every claim
    has supporting evidence.
    """

    results = []

    # --------------------------------------------------------
    # No claims
    # --------------------------------------------------------

    if not claims:

        return {
            "overall_verification":
                "UNSUPPORTED",

            "claims":
                []
        }

    # --------------------------------------------------------
    # Verify each claim
    # --------------------------------------------------------

    for claim in claims:

        result = verify_claim(
            claim,
            retrieved_chunks
        )

        results.append({

            "claim":
                result["claim"],

            "verification":
                result["verification"],

            "supporting_evidence":
                result["supporting_evidence"],

            "best_similarity":
                result["best_similarity"],

            "best_word_coverage":
                result["best_word_coverage"],

            "reason":
                result["reason"],
        })

    # --------------------------------------------------------
    # Overall verification
    # --------------------------------------------------------

    all_supported = all(
        item["verification"] == "SUPPORTED"
        for item in results
    )

    if all_supported:

        overall = "SUPPORTED"

    else:

        overall = "UNSUPPORTED"

    return {

        "overall_verification":
            overall,

        "claims":
            results
    }


# ============================================================
# LOCAL TESTS
# ============================================================

if __name__ == "__main__":

    test_chunks = [

        {
            "document_id":
                "test",

            "document_name":
                "test.pdf",

            "chunk_id":
                1,

            "text":
                """
                Deep Learning is a subset of machine learning
                based on artificial neural networks for
                predictive analysis.
                """
        },

        {
            "document_id":
                "research",

            "document_name":
                "AIResearchareasresearchgate-2025.pdf",

            "chunk_id":
                9,

            "text":
                """
                Reinforcement learning (RL) enhances
                decision-making in dynamic environments.
                Sutton and Barto are cited in connection
                with reinforcement learning.
                """
        },

        {
            "document_id":
                "research",

            "document_name":
                "AIResearchareasresearchgate-2025.pdf",

            "chunk_id":
                62,

            "text":
                """
                Sutton, R. S., & Barto, A. G. (1998).
                Reinforcement learning: An introduction.
                Cambridge: MIT Press.
                """
        }
    ]

    test_claims = [

        (
            "SUPPORTED RELATIONSHIP",
            "Deep learning is a subset of machine learning."
        ),

        (
            "UNSUPPORTED HISTORICAL CLAIM",
            "Sutton and Barto introduced reinforcement learning."
        ),

        (
            "UNSUPPORTED MEDICAL CLAIM",
            "Machine learning was first developed for medical diagnosis."
        ),

        (
            "SUPPORTED NEURAL NETWORK CLAIM",
            "Deep learning uses artificial neural networks."
        ),
    ]

    print("=" * 70)
    print("STRICT CLAIM VERIFICATION TEST")
    print("=" * 70)

    for name, claim in test_claims:

        result = verify_claim(
            claim,
            test_chunks
        )

        print("\n" + "-" * 70)

        print("TEST:")
        print(name)

        print("\nCLAIM:")
        print(claim)

        print("\nRESULT:")
        print(
            result["verification"]
        )

        print("\nREASON:")
        print(
            result["reason"]
        )

        print("\nSUPPORTING EVIDENCE:")

        if not result["supporting_evidence"]:

            print("None")

        else:

            for evidence in result[
                "supporting_evidence"
            ]:

                print(
                    f"- {evidence['document_name']} "
                    f"| Chunk {evidence['chunk_id']} "
                    f"| Coverage: "
                    f"{evidence['word_coverage']}"
                )

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)