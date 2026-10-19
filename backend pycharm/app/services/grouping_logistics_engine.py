"""
Student-Count Grouping & Logistics Engine for Civic Education.
Calculates optimal group partitions, resolves odd-count remainders,
and assigns explicit student roles to eliminate passive bystanders.
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field


class StudentRoleAssignment(BaseModel):
    role_name: str
    responsibility: str


class GroupingLogisticsResult(BaseModel):
    student_count: int
    total_groups: int
    group_sizes: List[int]
    group_summary_label: str
    roles_assigned: List[StudentRoleAssignment]
    pedagogy_adaptation: str
    materials_multiplier: int


# Canonical Civic Education Cooperative Roles
CIVIC_ROLES_5 = [
    StudentRoleAssignment(
        role_name="Leader / Facilitator",
        responsibility="Guides the team discussion, ensures everyone speaks, and keeps focus on the prompt."
    ),
    StudentRoleAssignment(
        role_name="Scribe / Secretary",
        responsibility="Records team arguments, writes key findings on the task sheet or notebook."
    ),
    StudentRoleAssignment(
        role_name="Timekeeper & Logistics",
        responsibility="Monitors the 30-minute pacing and collects/returns materials from the teacher."
    ),
    StudentRoleAssignment(
        role_name="Spokesperson / Presenter",
        responsibility="Presents the group's resolution or roleplay dialogue to the whole class."
    ),
    StudentRoleAssignment(
        role_name="Civic Investigator / Inquirer",
        responsibility="Checks accuracy against textbook facts and challenges assumptions."
    )
]

CIVIC_ROLE_6TH = StudentRoleAssignment(
    role_name="Creative Director / Chart Lead",
    responsibility="Coordinates the visual layout, chart illustrations, or roleplay freeze-frame staging."
)

CIVIC_ROLES_4 = [
    StudentRoleAssignment(
        role_name="Leader & Inquirer",
        responsibility="Facilitates discussion, asks probing questions, and guides decision-making."
    ),
    StudentRoleAssignment(
        role_name="Scribe / Recorder",
        responsibility="Synthesizes group consensus and writes the official notes."
    ),
    StudentRoleAssignment(
        role_name="Resource & Time Manager",
        responsibility="Monitors developmental phase minutes and handles charts/station cue cards."
    ),
    StudentRoleAssignment(
        role_name="Spokesperson / Presenter",
        responsibility="Delivers final findings during the plenary review session."
    )
]


class GroupingLogisticsEngine:
    """
    Deterministic partitioning engine for classroom sizes from 5 to 80 students.
    """

    @staticmethod
    def calculate_grouping(
        student_count: int,
        pedagogy_type: str = "Standard Jigsaw / Investigation"
    ) -> GroupingLogisticsResult:
        """
        Calculates group count, partitions odd remainders, and assigns distinct roles.
        Target group size: 5 students (allowed range: 4 to 6).
        """
        N = max(5, min(student_count, 80))

        # Target partition size calculation
        # If N <= 8: 2 small groups of 3-4
        if N <= 8:
            k = 2
        elif N <= 15:
            k = max(2, round(N / 4.5))
        elif N <= 45:
            k = max(3, round(N / 5.0))
        else:
            # Large classrooms (46 to 80 students)
            k = max(8, round(N / 5.5))

        base_size = N // k
        remainder = N % k

        # Distribute remainder by incrementing sizes of first 'remainder' groups
        group_sizes = []
        for i in range(k):
            size = base_size + (1 if i < remainder else 0)
            group_sizes.append(size)

        # Build descriptive label (e.g. "7 groups: 5 groups of 5 and 2 groups of 6")
        counts_by_size: Dict[int, int] = {}
        for sz in group_sizes:
            counts_by_size[sz] = counts_by_size.get(sz, 0) + 1

        parts = [f"{cnt} groups of {sz}" for sz, cnt in sorted(counts_by_size.items())]
        summary_label = f"{k} teams ({', '.join(parts)})"

        # Determine roles based on max group size
        max_size = max(group_sizes)
        if max_size >= 6:
            roles = CIVIC_ROLES_5 + [CIVIC_ROLE_6TH]
        elif max_size == 5:
            roles = CIVIC_ROLES_5
        else:
            roles = CIVIC_ROLES_4

        # Adaptation advice for Sri Lankan classroom contexts
        if N > 50:
            pedagogy_note = (
                f"Large class management ({N} students): Station materials must be duplicated across "
                f"{k} clusters. Pairs within each team work on sub-questions before combining."
            )
        elif N < 15:
            pedagogy_note = (
                f"Small class focus ({N} students): Deep conversational seminar or 2-sided mock council debate."
            )
        else:
            pedagogy_note = (
                f"Standard class layout ({N} students): Desks rearranged into {k} islands. "
                "Rotating roles allow every student active participation without bystanders."
            )

        return GroupingLogisticsResult(
            student_count=N,
            total_groups=k,
            group_sizes=group_sizes,
            group_summary_label=summary_label,
            roles_assigned=roles,
            pedagogy_adaptation=pedagogy_note,
            materials_multiplier=k
        )