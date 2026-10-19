"""
Multi-Period Learning Outcome Allocator Engine for Civic Education.
Guarantees sequence consistency (Period 1 and Period 2 requests yield identical mapping)
and handles outcome spanning so no period is ever left empty.
Extracts verbatim NIE outcomes from Teacher Instructional Guide (TIG) context
and constructs deterministic, cognitively sequenced multi-period progression plans
following the pedagogical cycle: Introduced -> Developed -> Practiced -> Assessed.
"""

import re
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("OutcomeAllocator")

# Cognitive weights matching Bloom's Taxonomy in Sri Lankan NIE Curriculum
COGNITIVE_WEIGHTS: Dict[str, int] = {
    # Level 1: Remember / Recall (Introduce)
    "name": 1, "names": 1, "list": 1, "lists": 1, "state": 1, "states": 1,
    "identify": 1, "identifies": 1, "define": 1, "defines": 1, "recall": 1,

    # Level 2: Understand / Clarify (Develop)
    "describe": 2, "describes": 2, "explain": 2, "explains": 2, "discuss": 2, "discusses": 2,
    "distinguish": 2, "distinguishes": 2, "compare": 2, "compares": 2, "clarify": 2,

    # Level 3: Apply / Analyze (Practice)
    "demonstrate": 3, "demonstrates": 3, "investigate": 3, "investigates": 3,
    "simulate": 3, "simulates": 3, "analyze": 3, "analyzes": 3, "examine": 3, "illustrate": 3,

    # Level 4: Evaluate / Create / Civic Action (Assess & Synthesize)
    "evaluate": 4, "evaluates": 4, "appreciate": 4, "appreciates": 4, "value": 4, "values": 4,
    "propose": 4, "proposes": 4, "formulate": 4, "advocate": 4, "judge": 4, "construct": 4
}


def clean_bullet(text: str) -> str:
    """
    Cleans up whitespaces, strips symbols, removes parenthetical notes,
    and trims to a proper punctuated sentence.
    """
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = re.sub(r"^[\u2022\u2023\u25E6\u2043\u2219\*\-\–\—\d+\.]\s*", "", cleaned).strip()
    return cleaned


def calculate_cognitive_weight(outcome_text: str) -> int:
    """Calculates cognitive complexity score (1 to 4) based on action verb analysis."""
    text_lower = outcome_text.lower()
    for verb, weight in COGNITIVE_WEIGHTS.items():
        if re.search(r'\b' + re.escape(verb) + r'\b', text_lower):
            return weight
    return 2  # Default to understanding level


def extract_verbatim_tig_outcomes(tig_text: str, competency_level: str = "") -> List[str]:
    """
    Extracts official learning outcomes verbatim from the TIG text.
    Uses regex pattern matching against Sri Lankan NIE curriculum guide tabular structures.
    Does NOT rewrite or synthesize wording.
    """
    if not tig_text or not tig_text.strip():
        return []

    outcomes: List[str] = []

    # 1. Clean bullet/numbered lines after 'Learning Outcomes' or 'ඉගෙනුම් ඵල' headers
    patterns = [
        # Pattern A: Tabular lines or markdown bullets
        r"(?:Learning Outcomes|Learning Outcome|Specific Outcomes|Outcomes)[\s\S]*?(?=\n\s*(?:Suggested Learning Activities|Teaching Learning Activities|Competency|Duration|$))",
        # Pattern B: Lines prefixed with outcome markers like 1., 2., •, -, a)
        r"(?:^|\n)\s*(?:•|\*|-|\d+\.|\([a-z]\))\s+([A-Z][^\n]{15,})"
    ]

    for pat in patterns:
        matches = re.findall(pat, tig_text, re.IGNORECASE)
        if matches:
            for m in matches:
                if isinstance(m, str):
                    clean_lines = [
                        line.strip().lstrip("•*-123456789.() ")
                        for line in m.split("\n")
                        if len(line.strip()) > 15
                    ]
                    for line in clean_lines:
                        # Reject column header names
                        if not any(header in line.lower() for header in ["suggested", "competency", "time", "learning-teaching"]):
                            c = clean_bullet(line)
                            if c not in outcomes:
                                outcomes.append(c)

    # 2. Fallback: Parse explicit bullet lines containing educational action verbs
    if not outcomes:
        lines = tig_text.split("\n")
        for line in lines:
            line_str = line.strip().lstrip("•*-123456789.() ")
            first_word = line_str.split(" ")[0].lower() if line_str else ""
            if first_word in COGNITIVE_WEIGHTS and len(line_str) > 20:
                c = clean_bullet(line_str)
                if c not in outcomes:
                    outcomes.append(c)

    logger.info("Extracted %d verbatim outcome(s) for Competency Level %s", len(outcomes), competency_level)
    return outcomes


def extract_civic_tig_learning_outcomes(
    tig_text: str,
    competency_level: str,
) -> List[str]:
    """Extract only the selected competency's official TIG Learning Outcomes section."""
    if not tig_text or not competency_level.strip():
        return []

    level = re.escape(competency_level.strip())
    competency_header = re.compile(
        r"^\s*Competency\s*Level\s*[:;]?\s*(?:\n\s*[:;]?\s*)?"
        r"(\d+(?:\.\d+)+)\s*$",
        re.IGNORECASE | re.MULTILINE,
    )
    headers = list(competency_header.finditer(tig_text))
    target_header = next(
        (header for header in headers if header.group(1) == competency_level.strip()),
        None,
    )
    if target_header is None:
        inline_header = re.search(
            rf"^\s*Competency\s*Level\s*[:;]?\s*{level}\s*$",
            tig_text,
            re.IGNORECASE | re.MULTILINE,
        )
        if inline_header is None:
            return []
        section_start = inline_header.start()
        section_end = len(tig_text)
    else:
        section_start = target_header.start()
        next_header = next(
            (
                header
                for header in headers
                if header.start() > target_header.start()
                and header.group(1) != competency_level.strip()
            ),
            None,
        )
        section_end = next_header.start() if next_header else len(tig_text)

    competency_text = tig_text[section_start:section_end]
    lines = competency_text.splitlines()
    outcome_header = re.compile(
        r"^\s*(?:learning\s+outcomes?|specific\s+outcomes?)\s*:?\s*$",
        re.IGNORECASE,
    )
    section_stop = re.compile(
        r"^\s*(?:instructions?\s+for\s+lesson\s+planning|"
        r"suggested\s+learning\s+activities|subject\s+content|"
        r"quality\s+inputs?|instructions?\s+for\s+assessment)\b",
        re.IGNORECASE,
    )
    action_verb = re.compile(
        r"^(?:identif(?:y|ies)|explain(?:s)?|investigat(?:e|es)|present(?:s)?|"
        r"name(?:s)?|describ(?:e|es)|list(?:s)?|suggest(?:s)?|demonstrat(?:e|es)|"
        r"analy[sz](?:e|es)|evaluat(?:e|es)|compar(?:e|es)|giv(?:e|es)|"
        r"express(?:es)?|appreciat(?:e|es)|classif(?:y|ies)|defin(?:e|es)|"
        r"distinguish(?:es)?|show(?:s)?|build(?:s)?|prepar(?:e|es)|stat(?:e|es)|"
        r"emphasi[sz](?:e|es)|accept(?:s)?|valu(?:e|es)|mak(?:e|es)|"
        r"formulat(?:e|es)|construct(?:s)?|illustrat(?:e|es)|observ(?:e|es)|"
        r"record(?:s)?|draw(?:s)?|calculat(?:e|es)|design(?:s)?|measur(?:e|es)|"
        r"determin(?:e|es)|conduct(?:s)?|inf(?:er|ers)|predict(?:s)?|"
        r"verify|verifies|recogniz(?:e|es)|participat(?:e|es)|contribut(?:e|es)|"
        r"practi[cs](?:e|es)|read(?:s)?|writ(?:e|es)|find(?:s)?|perform(?:s)?|"
        r"understand(?:s)?|us(?:e|es)|act(?:s)?|take\s+part\s+in)\b",
        re.IGNORECASE,
    )
    bullet = re.compile(r"^\s*[\u2022\u2023\u25E6\u2043\u2219\uFFFD*\-–—]\s*(.*)$")

    in_outcomes = False
    outcomes: List[str] = []
    current_outcome = ""

    def append_current() -> None:
        nonlocal current_outcome
        outcome = re.sub(r"\s+", " ", current_outcome).strip()
        outcome = re.sub(r"\s+([.,;:])", r"\1", outcome)
        if outcome and outcome not in outcomes:
            outcomes.append(outcome)
        current_outcome = ""

    for line in lines:
        stripped = line.strip()
        if not in_outcomes:
            if outcome_header.match(stripped):
                in_outcomes = True
            continue
        if section_stop.match(stripped):
            append_current()
            break
        if not stripped or stripped == ":":
            continue

        bullet_match = bullet.match(line)
        if bullet_match:
            bullet_text = bullet_match.group(1).strip()
            if not bullet_text:
                continue
            append_current()
            current_outcome = bullet_text
            continue

        if action_verb.match(stripped):
            append_current()
            current_outcome = stripped
        elif current_outcome and stripped in {".", ",", ";"}:
            current_outcome += stripped
        elif current_outcome:
            current_outcome = f"{current_outcome} {stripped}"

    append_current()
    logger.info(
        "Extracted %d official Civic Education TIG learning outcome(s) for Competency Level %s",
        len(outcomes),
        competency_level,
    )
    return outcomes


class MultiPeriodOutcomeAllocationPlan:
    """
    Deterministic progression allocation with guaranteed consistency and outcome spanning.
    Calling get_outcomes_for_period(1) and get_outcomes_for_period(2) at separate times
    yields the exact same distribution.
    """

    def __init__(self, competency_level: str, total_periods: int, all_outcomes: List[str]):
        self.competency_level = competency_level
        self.total_periods = max(1, min(total_periods, 4))
        # Stable deduplication preserving order
        deduped = []
        for o in all_outcomes:
            c = clean_bullet(o)
            if c and c not in deduped:
                deduped.append(c)
        self.all_outcomes = deduped

        # Period to outcomes mapping
        self.period_allocations: Dict[int, List[str]] = {p: [] for p in range(1, self.total_periods + 1)}

        # Progression state: {period: {outcome: "Introduced" | "Developed" | "Practiced" | "Assessed"}}
        self.progression_matrix: Dict[int, Dict[str, str]] = {p: {} for p in range(1, self.total_periods + 1)}

        self._build_deterministic_matrix()

    def _build_deterministic_matrix(self):
        if not self.all_outcomes:
            return

        # 1. Deterministic Cognitive Ordering (sort by Bloom score, secondary tiebreak by outcome string)
        sorted_outcomes = sorted(self.all_outcomes, key=lambda x: (calculate_cognitive_weight(x), x))
        n_outcomes = len(sorted_outcomes)

        # -------------------------------------------------------------
        # 1 PERIOD CONFIGURATION
        # -------------------------------------------------------------
        if self.total_periods == 1:
            self.period_allocations[1] = sorted_outcomes
            for o in sorted_outcomes:
                self.progression_matrix[1][o] = "Introduced, Developed & Formatively Assessed"
            return

        # -------------------------------------------------------------
        # OUTCOME SPANNING & PARTITIONING (2, 3, or 4 Periods)
        # -------------------------------------------------------------
        base_size = n_outcomes // self.total_periods
        remainder = n_outcomes % self.total_periods

        start = 0
        stages = [
            "Introduced & Explored (Foundational Inquiry)",
            "Developed & Investigated (Group Deepening / Active Analysis)",
            "Practiced & Applied (Simulation / Real-world Application)",
            "Synthesized & Formatively Assessed (Evaluation & Action Plan)"
        ]

        for p in range(1, self.total_periods + 1):
            chunk_size = base_size + (1 if p <= remainder else 0)

            # --- OUTCOME SPANNING RULE ---
            # If outcome count is smaller than periods count (e.g., 2 outcomes across 3 periods)
            if chunk_size == 0 or start >= n_outcomes:
                # The outcome from previous period spans into this period with advanced stage
                spanned_outcome = sorted_outcomes[-1]
                self.period_allocations[p] = [spanned_outcome]
                stage_label = f"Spanned: {stages[min(p - 1, 3)]}"
                self.progression_matrix[p][spanned_outcome] = stage_label
                continue

            end = start + chunk_size
            chunk = sorted_outcomes[start:end]
            start = end

            self.period_allocations[p] = chunk
            for o in chunk:
                # Stage corresponds to period position relative to total sequence
                stage_idx = int(((p - 1) / max(1, self.total_periods - 1)) * 3)
                self.progression_matrix[p][o] = stages[stage_idx]

    def get_outcomes_for_period(self, requested_period: int) -> List[str]:
        """
        Retrieves the exact allocated outcomes for a requested period.
        Deterministic: Independent queries for Period 1, Period 2 produce the exact sequence.
        """
        clamped_p = max(1, min(requested_period, self.total_periods))
        return self.period_allocations.get(clamped_p, self.all_outcomes)

    def get_stage_description(self, requested_period: int, outcome: str) -> str:
        """Returns the specific pedagogical stage assigned to an outcome in a given period."""
        clamped_p = max(1, min(requested_period, self.total_periods))
        return self.progression_matrix.get(clamped_p, {}).get(outcome, "Active Instructional Focus")

    def get_progression_summary_for_period(self, requested_period: int) -> str:
        """Returns a string formatted for LLM prompt context."""
        clamped_p = max(1, min(requested_period, self.total_periods))
        assigned = self.period_allocations.get(clamped_p, [])
        lines = []
        for o in assigned:
            stage = self.progression_matrix[clamped_p].get(o, "Active Learning Stage")
            lines.append(f"• {o} -> Pedagogical Stage: [{stage}]")
        return "\n".join(lines)

    def restore_period_allocations(self, allocations: Dict[int, List[str]]) -> bool:
        """Restores a previously saved complete allocation when its outcomes still match."""
        if set(allocations) != set(range(1, self.total_periods + 1)):
            return False
        if any(
            not isinstance(outcomes, list)
            or any(outcome not in self.all_outcomes for outcome in outcomes)
            for outcomes in allocations.values()
        ):
            return False
        if set(outcome for outcomes in allocations.values() for outcome in outcomes) != set(self.all_outcomes):
            return False

        self.period_allocations = {
            period: list(allocations[period])
            for period in range(1, self.total_periods + 1)
        }
        stage_names = [
            "Introduced & Explored (Foundational Inquiry)",
            "Developed & Investigated (Group Deepening / Active Analysis)",
            "Practiced & Applied (Simulation / Real-world Application)",
            "Synthesized & Formatively Assessed (Evaluation & Action Plan)",
        ]
        self.progression_matrix = {period: {} for period in range(1, self.total_periods + 1)}
        for period, outcomes in self.period_allocations.items():
            stage_index = (
                0
                if self.total_periods == 1
                else int(((period - 1) / max(1, self.total_periods - 1)) * 3)
            )
            stage = stage_names[stage_index]
            for outcome in outcomes:
                self.progression_matrix[period][outcome] = stage
        return True


def allocate_learning_outcomes_across_periods(
    all_outcomes: List[str],
    periods: int = 1,
    competency_level: str = "8.1.1"
) -> MultiPeriodOutcomeAllocationPlan:
    """Factory helper to build and return the allocation plan."""
    return MultiPeriodOutcomeAllocationPlan(
        competency_level=competency_level,
        total_periods=periods,
        all_outcomes=all_outcomes
    )