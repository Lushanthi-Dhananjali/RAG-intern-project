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
    cleaned = re.sub(r"\s*\([^)]*plan the lesson[^)]*\)", "", cleaned, flags=re.IGNORECASE).strip()
    if cleaned and not cleaned.endswith((".", ";")):
        cleaned += "."
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