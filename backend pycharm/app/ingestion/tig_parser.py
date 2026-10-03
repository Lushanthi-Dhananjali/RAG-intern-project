import os
import re
from typing import List, Dict, Any


class TIGCurriculumUnitParser:
    """
    Parses National Curriculum Teacher Instructional Guides (TIG)
    into structured units supporting 3-digit Competency Levels (e.g., 1.1.1, 8.2.1).
    """

    @staticmethod
    def extract_curriculum_units(
            raw_text: str,
            file_name: str,
            grade_level: str,
            subject: str = "Civic Education"
    ) -> List[Dict[str, Any]]:
        # Regex to capture 3-digit competency levels (e.g., 1.1.1, 8.2.1) or 2-digit levels (e.g., 1.1)
        comp_level_pattern = r"(?:Competenc(?:e|y)\s*Level\s*[:\-]?\s*|\bLevel\s*[:\-]?\s*)(\d+\.\d+(?:\.\d+)?)"

        splits = re.split(comp_level_pattern, raw_text, flags=re.IGNORECASE)
        curriculum_units = []

        # Track main parent competence (e.g., "1.0", "8.0")
        current_parent_comp = "General Competence"
        if splits:
            preamble = splits[0]
            parent_match = re.search(r"Competenc(?:e|y)\s*[:\-]?\s*(\d+(?:\.\d+)?)", preamble, re.IGNORECASE)
            if parent_match:
                current_parent_comp = f"Competency {parent_match.group(1)}"

        i = 1
        while i < len(splits):
            comp_level = splits[i].strip()  # e.g., "1.1.1" or "8.2.1"
            content_block = splits[i + 1].strip()  # Content belonging to this level

            # Update parent competency if explicitly defined in block
            parent_match = re.search(r"Competenc(?:e|y)\s*[:\-]?\s*(\d+(?:\.0)?)", content_block, re.IGNORECASE)
            if parent_match:
                current_parent_comp = f"Competency {parent_match.group(1)}"
            elif "." in comp_level:
                major_num = comp_level.split(".")[0]
                current_parent_comp = f"Competency {major_num}.0"

            # Extract TIG sub-sections
            periods = TIGCurriculumUnitParser._extract_field(
                content_block,
                r"(?:No\.?\s*of\s*Periods?|Time\s*Allocat\w+|Periods?)\s*[:\-]?\s*(\d+\s*(?:periods?|hours?|mins?)?)",
                default="01 Period (40 mins)"
            )

            learning_outcomes = TIGCurriculumUnitParser._extract_section(
                content_block,
                start_patterns=[r"Learning\s*Outcomes?", r"Unique\s*Learning\s*Outcomes?", r"Objectives?"],
                end_patterns=[r"Syllabus\s*Content", r"Subject\s*Matter", r"Suggested\s*Activities", r"Competenc"]
            )

            syllabus_content = TIGCurriculumUnitParser._extract_section(
                content_block,
                start_patterns=[r"Syllabus\s*Content", r"Subject\s*Matter", r"Content"],
                end_patterns=[r"Suggested\s*Activities?", r"Learning\s*Teaching\s*Activities?", r"Competenc"]
            )

            suggested_activities = TIGCurriculumUnitParser._extract_section(
                content_block,
                start_patterns=[r"Suggested\s*Activities?", r"Learning\s*Teaching\s*Activities?", r"Instructions?"],
                end_patterns=[r"Assessment", r"Evaluation", r"Competenc"]
            )

            # Build unified chunk content for vector storage
            chunk_content = (
                f"Subject: {subject} | Grade: {grade_level}\n"
                f"Competence: {current_parent_comp}\n"
                f"Competence Level: {comp_level}\n"
                f"Time Allocation: {periods}\n\n"
                f"--- UNIQUE LEARNING OUTCOMES ---\n{learning_outcomes}\n\n"
                f"--- SYLLABUS CONTENT ---\n{syllabus_content}\n\n"
                f"--- SUGGESTED TEACHING-LEARNING ACTIVITIES ---\n{suggested_activities}\n"
            )

            sanitized_file = re.sub(r"[^a-zA-Z0-9_-]", "_", os.path.splitext(file_name)[0])
            unit_id = f"{sanitized_file}_comp_{comp_level.replace('.', '_')}"

            curriculum_units.append({
                "id": unit_id,
                "content": chunk_content.strip(),
                "metadata": {
                    "source": file_name,
                    "grade_level": grade_level,
                    "subject": subject,
                    "competence": current_parent_comp,
                    "competence_level": comp_level,
                    "periods": periods,
                    "doc_type": "teacher_guide"
                }
            })

            i += 2

        return curriculum_units

    @staticmethod
    def _extract_field(text: str, pattern: str, default: str = "") -> str:
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1).strip() if match else default

    @staticmethod
    def _extract_section(text: str, start_patterns: List[str], end_patterns: List[str]) -> str:
        starts = "|".join(start_patterns)
        ends = "|".join(end_patterns)
        pattern = rf"(?:{starts})\s*[:\-]?\s*(.*?)(?=(?:{ends})|\Z)"
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
        return "Refer to official syllabus guidelines."