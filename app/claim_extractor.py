import re


# ============================================================
# CLAIM EXTRACTION
# ============================================================

def extract_claims(answer: str) -> list[str]:
    """
    Extract factual claims from a generated answer.

    This extractor does NOT use an LLM.

    Goals:
    - Split independent factual statements.
    - Split simple compound claims joined by "and".
    - Preserve the subject when pronouns such as "it" are used.
    - Remove obvious reasoning/meta text.
    - Never invent information.
    """

    if not answer:
        return []

    answer = answer.strip()

    # --------------------------------------------------------
    # SPECIAL CASE
    # --------------------------------------------------------

    if answer.upper() == "NOT ENOUGH EVIDENCE":
        return []

    # --------------------------------------------------------
    # CLEAN MARKDOWN
    # --------------------------------------------------------

    # Remove bold markers.
    answer = re.sub(r"\*\*(.*?)\*\*", r"\1", answer)

    # Remove italic markers.
    answer = re.sub(r"(?<!\*)\*(.*?)(?<!\*)\*", r"\1", answer)

    # Remove inline code markers.
    answer = re.sub(r"`(.*?)`", r"\1", answer)

    # Normalize whitespace.
    answer = re.sub(r"\s+", " ", answer).strip()

    # --------------------------------------------------------
    # REMOVE COMMON LIST MARKERS
    # --------------------------------------------------------

    answer = re.sub(
        r"(?m)^\s*(?:\d+[\.\)]|[-*])\s+",
        "",
        answer
    )

    # --------------------------------------------------------
    # SPLIT INTO SENTENCES
    # --------------------------------------------------------

    sentences = re.split(
        r"(?<=[.!?])\s+",
        answer
    )

    claims = []

    # --------------------------------------------------------
    # SUBJECT TRACKING
    # --------------------------------------------------------

    last_subject = None

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        # ----------------------------------------------------
        # REMOVE OBVIOUS META / REASONING SENTENCES
        # ----------------------------------------------------

        lower = sentence.lower()

        ignored_prefixes = (
            "let me ",
            "i need to ",
            "i will ",
            "we are given ",
            "we have ",
            "the user asks ",
            "the user question ",
            "the question asks ",
            "the evidence states ",
            "from the evidence ",
            "according to the instructions ",
            "i should ",
            "i must ",
            "we must ",
            "we need to ",
            "the provided evidence ",
            "the provided information ",
            "here is ",
            "here are ",
        )

        if lower.startswith(ignored_prefixes):
            continue

        # ----------------------------------------------------
        # REMOVE COMMON META PHRASES AT THE BEGINNING
        # ----------------------------------------------------

        sentence = re.sub(
            r"^(from the evidence|according to the document|"
            r"according to the paper)\s*:?\s*",
            "",
            sentence,
            flags=re.IGNORECASE
        ).strip()

        if not sentence:
            continue

        # ----------------------------------------------------
        # DETECT SUBJECT
        # ----------------------------------------------------

        subject_match = re.match(
            r"^([A-Z][A-Za-z0-9\-]*(?:\s+[A-Za-z][A-Za-z0-9\-]*){0,5})\s+"
            r"(?:is|are|was|were|has|have|uses|supports|focuses|"
            r"allows|enables|includes|contains|refers|means|"
            r"consists|provides|improves|helps|uses)\b",
            sentence
        )

        if subject_match:
            candidate = subject_match.group(1).strip()

            # Avoid treating generic words as subjects.
            if candidate.lower() not in {
                "it",
                "this",
                "that",
                "the",
                "these",
                "those",
            }:
                last_subject = candidate

        # ----------------------------------------------------
        # SPLIT SIMPLE COMPOUND CLAIMS
        # ----------------------------------------------------

        compound_parts = split_compound_claim(sentence)

        for part in compound_parts:

            part = part.strip()

            if not part:
                continue

            # ------------------------------------------------
            # RESTORE SUBJECT FOR PRONOUNS
            # ------------------------------------------------

            part_lower = part.lower()

            if (
                last_subject
                and (
                    part_lower.startswith("it ")
                    or part_lower.startswith("it.")
                    or part_lower.startswith("it,")
                )
            ):

                part = re.sub(
                    r"^it\b",
                    last_subject,
                    part,
                    count=1,
                    flags=re.IGNORECASE
                )

            claims.append(part.strip())

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_claims = []

    seen = set()

    for claim in claims:

        normalized = claim.lower().strip()

        if normalized in seen:
            continue

        seen.add(normalized)

        unique_claims.append(claim)

    return unique_claims


# ============================================================
# COMPOUND CLAIM SPLITTER
# ============================================================

def split_compound_claim(sentence: str) -> list[str]:
    """
    Split simple independent factual clauses joined by 'and'.

    Examples:

    Machine learning was invented in 1950 and was first
    developed for medical diagnosis.

    ->
    Machine learning was invented in 1950.
    Machine learning was first developed for medical diagnosis.

    Deep learning is a subset of machine learning and uses
    artificial neural networks.

    ->
    Deep learning is a subset of machine learning.
    Deep learning uses artificial neural networks.
    """

    # --------------------------------------------------------
    # Do not split sentences containing certain structures
    # where "and" is probably part of the same phrase.
    # --------------------------------------------------------

    protected_patterns = [
        r"research and development",
        r"trial and error",
        r"input and output",
        r"cause and effect",
        r"terms and conditions",
        r"science and technology",
        r"artificial intelligence and machine learning",
    ]

    lower_sentence = sentence.lower()

    for pattern in protected_patterns:

        if re.search(pattern, lower_sentence):

            # Only continue if there is another likely
            # independent clause.
            pass

    # --------------------------------------------------------
    # Case 1:
    #
    # "X is A and is B"
    #
    # Split into:
    # "X is A"
    # "X is B"
    # --------------------------------------------------------

    match = re.match(
        r"^(.*?)\s+and\s+(is|are|was|were|has|have|"
        r"uses|supports|focuses|allows|enables|includes|"
        r"contains|refers|means|consists|provides|"
        r"improves|helps)\s+(.+)$",
        sentence,
        flags=re.IGNORECASE
    )

    if match:

        first_part = match.group(1).strip()

        verb = match.group(2).strip()

        second_part = match.group(3).strip()

        # Find subject of first clause.
        subject_match = re.match(
            r"^(.+?)\s+(is|are|was|were|has|have)\s+",
            first_part,
            flags=re.IGNORECASE
        )

        if subject_match:

            subject = subject_match.group(1).strip()

            return [
                first_part + ".",
                f"{subject} {verb} {second_part}".strip(". ") + "."
            ]

    # --------------------------------------------------------
    # Case 2:
    #
    # "X was A and was B"
    # --------------------------------------------------------

    match = re.match(
        r"^(.+?)\s+(is|are|was|were)\s+(.+?)\s+and\s+"
        r"(is|are|was|were)\s+(.+)$",
        sentence,
        flags=re.IGNORECASE
    )

    if match:

        subject = match.group(1).strip()

        first_verb = match.group(2).strip()

        first_predicate = match.group(3).strip()

        second_verb = match.group(4).strip()

        second_predicate = match.group(5).strip()

        return [
            f"{subject} {first_verb} {first_predicate}.",
            f"{subject} {second_verb} {second_predicate}."
        ]

    # --------------------------------------------------------
    # Case 3:
    #
    # "X was A and first B"
    #
    # Example:
    # Machine learning was invented in 1950 and first
    # developed for medical diagnosis.
    # --------------------------------------------------------

    match = re.match(
        r"^(.+?)\s+(was|were|is|are)\s+(.+?)\s+and\s+"
        r"(first|also|then)\s+(.+)$",
        sentence,
        flags=re.IGNORECASE
    )

    if match:

        subject = match.group(1).strip()

        verb = match.group(2).strip()

        first_predicate = match.group(3).strip()

        connector = match.group(4).strip()

        second_predicate = match.group(5).strip()

        return [
            f"{subject} {verb} {first_predicate}.",
            f"{subject} {verb} {connector} {second_predicate}."
        ]

    # --------------------------------------------------------
    # Case 4:
    #
    # "X was A and B"
    #
    # Only split if the second part clearly looks like a
    # separate predicate.
    # --------------------------------------------------------

    match = re.match(
        r"^(.+?)\s+(is|are|was|were)\s+(.+?)\s+and\s+(.+)$",
        sentence,
        flags=re.IGNORECASE
    )

    if match:

        subject = match.group(1).strip()

        verb = match.group(2).strip()

        first_predicate = match.group(3).strip()

        second_predicate = match.group(4).strip()

        # Avoid splitting short coordinated descriptions
        # such as "red and blue".
        if len(first_predicate.split()) >= 3:

            return [
                f"{subject} {verb} {first_predicate}.",
                f"{subject} {verb} {second_predicate}."
            ]

    # --------------------------------------------------------
    # No safe split.
    # --------------------------------------------------------

    return [sentence]


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    test_answers = [

        # TEST 1
        (
            "Machine learning allows machines to learn and improve "
            "from experience automatically."
        ),

        # TEST 2
        (
            "Machine learning allows machines to learn and improve "
            "from experience automatically. It was invented in 1950."
        ),

        # TEST 3
        (
            "Machine learning was invented in 1950 and was first "
            "developed for medical diagnosis."
        ),

        # TEST 4
        (
            "Deep Learning is a subset of machine learning. "
            "It uses artificial neural networks."
        ),

        # TEST 5
        (
            "Machine learning is a branch of artificial intelligence "
            "and is used for prediction."
        ),

        # TEST 6
        (
            "NOT ENOUGH EVIDENCE"
        ),

        # TEST 7
        (
            "We are given a document. Machine learning is a branch "
            "of artificial intelligence."
        ),

        # TEST 8
        (
            "Machine learning focuses on algorithms and supports "
            "data-driven decision making."
        ),

        # TEST 9
        (
            "Deep learning is a subset of machine learning and uses "
            "artificial neural networks."
        ),

        # TEST 10
        (
            "Machine learning was invented in 1950 and was first "
            "developed for medical diagnosis."
        ),

        # TEST 11
        (
            "Machine learning is a branch of artificial intelligence "
            "and is used for prediction."
        ),
    ]


    for i, answer in enumerate(
        test_answers,
        start=1
    ):

        print("=" * 60)
        print(f"TEST {i}")
        print("=" * 60)

        print("\nAnswer:")
        print(answer)

        claims = extract_claims(answer)

        print("\nExtracted claims:")

        if not claims:

            print("No factual claims.")

        else:

            for number, claim in enumerate(
                claims,
                start=1
            ):

                print(f"{number}. {claim}")