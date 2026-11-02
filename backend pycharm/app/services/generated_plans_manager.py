import os
import re
import json
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

logger = logging.getLogger("GeneratedPlansManager")

# Resolve absolute path to 'generated_plans' directory inside 'backend pycharm'
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GENERATED_PLANS_DIR = os.path.join(BASE_DIR, "generated_plans")


def ensure_directory_exists() -> str:
    """Ensures the generated_plans directory exists and returns its absolute path."""
    if not os.path.exists(GENERATED_PLANS_DIR):
        os.makedirs(GENERATED_PLANS_DIR, exist_ok=True)
    return GENERATED_PLANS_DIR


def _sanitize_filename(filename: str) -> str:
    """Sanitizes filename and prevents directory traversal attacks."""
    clean_name = os.path.basename(filename.strip())
    if not clean_name.lower().endswith(".json"):
        clean_name += ".json"
    return clean_name


URL_PATTERN = re.compile(r"https?://|www\.", re.IGNORECASE)


def _sanitize_plan_dict(content: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitizes plan dictionary to ensure competence and competence_level never contain URLs."""
    if not isinstance(content, dict):
        return content

    comp_level = str(content.get("competence_level", "")).strip()
    if URL_PATTERN.search(comp_level):
        code_match = re.search(r"\b(\d+\.\d+(?:\.\d+)?)\b", comp_level)
        content["competence_level"] = code_match.group(1) if code_match else "8.1.1"

    competence = str(content.get("competence", "")).strip()
    if URL_PATTERN.search(competence):
        clean_code = str(content.get("competence_level", "8.1.1")).strip()
        from app.services.timing_guardrail_engine import resolve_clean_competence_title
        content["competence"] = resolve_clean_competence_title(clean_code, fallback_text=str(content.get("lesson", "")))

    lesson = str(content.get("lesson", "")).strip()
    if URL_PATTERN.search(lesson):
        content["lesson"] = re.sub(r"https?://\S+", "", lesson).strip() or "Lesson Plan"

    return content


def _get_safe_filepath(filename: str) -> Optional[str]:
    """Resolves and validates that the file is strictly inside GENERATED_PLANS_DIR."""
    clean_name = _sanitize_filename(filename)
    safe_dir = os.path.abspath(ensure_directory_exists())
    target_path = os.path.abspath(os.path.join(safe_dir, clean_name))

    # Path traversal protection
    if not target_path.startswith(safe_dir):
        logger.warning("Path traversal attempt detected: %s", filename)
        return None

    return target_path


def list_generated_plans(
    search: Optional[str] = None,
    grade: Optional[str] = None,
    subject: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Scans the generated_plans directory and returns summaries of all saved plans.
    Supports filtering by search keywords, grade level, and subject.
    """
    plans_dir = ensure_directory_exists()
    summaries: List[Dict[str, Any]] = []

    try:
        entries = os.listdir(plans_dir)
    except OSError as err:
        logger.error("Failed to list files in %s: %s", plans_dir, err)
        return []

    json_files = [f for f in entries if f.lower().endswith(".json")]

    for fname in json_files:
        filepath = os.path.join(plans_dir, fname)
        if not os.path.isfile(filepath):
            continue

        try:
            stat_info = os.stat(filepath)
            created_dt = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)
            created_at_iso = created_dt.isoformat()

            with open(filepath, "r", encoding="utf-8") as f:
                content = json.load(f)
            content = _sanitize_plan_dict(content)

            plan_grade = str(content.get("grade", "Grade 8"))
            plan_subject = str(content.get("subject", "Civic Education"))
            comp_level = str(content.get("competence_level", ""))
            competence = str(content.get("competence", ""))
            lesson = str(content.get("lesson", ""))
            entrance = str(content.get("the_entrance", ""))
            summary_text = str(content.get("summary", ""))
            time_alloc = str(content.get("time_allocation", ""))
            steps = content.get("lesson_development_steps", [])
            outcomes = content.get("unique_learning_outcome", [])
            period_number = content.get("period_number")
            total_periods = content.get("total_periods")
            selected_activity_title = content.get("selected_activity_title")

            # Apply Grade Filter
            if grade and grade.strip() and grade.lower() != "all":
                target_g = grade.strip().lower()
                if target_g not in plan_grade.lower():
                    continue

            # Apply Subject Filter
            if subject and subject.strip() and subject.lower() != "all":
                target_s = subject.strip().lower()
                if target_s not in plan_subject.lower():
                    continue

            # Apply Search Query
            if search and search.strip():
                query = search.strip().lower()
                searchable_corpus = f"{fname} {comp_level} {competence} {lesson} {entrance} {summary_text} {plan_grade} {plan_subject}".lower()
                if query not in searchable_corpus:
                    continue

            plan_id = os.path.splitext(fname)[0]
            summaries.append({
                "id": plan_id,
                "filename": fname,
                "grade": plan_grade,
                "subject": plan_subject,
                "competence_level": comp_level,
                "period_number": period_number,
                "total_periods": total_periods,
                "selected_activity_title": selected_activity_title,
                "competence": competence,
                "lesson": lesson,
                "time_allocation": time_alloc,
                "the_entrance": entrance,
                "summary": summary_text,
                "step_count": len(steps) if isinstance(steps, list) else 0,
                "outcome_count": len(outcomes) if isinstance(outcomes, list) else 0,
                "created_at": created_at_iso,
                "file_size_bytes": stat_info.st_size,
            })

        except Exception as exc:
            logger.warning("Could not read or parse plan %s: %s", fname, exc)
            continue

    # Sort plans by competency, then period number when present, then filename.
    def sort_key(item: Dict[str, Any]):
        comp = item.get("competence_level", "")
        parts = [int(p) if p.isdigit() else p for p in comp.split(".")]
        period = item.get("period_number")
        return (parts, period if isinstance(period, int) else 0, item.get("filename", ""))

    try:
        summaries.sort(key=sort_key)
    except Exception:
        summaries.sort(key=lambda x: x.get("filename", ""))

    return summaries


def get_generated_plan(filename: str) -> Optional[Dict[str, Any]]:
    """
    Reads and returns the complete JSON payload of a generated plan by filename.
    """
    filepath = _get_safe_filepath(filename)
    if not filepath or not os.path.isfile(filepath):
        return None

    try:
        stat_info = os.stat(filepath)
        created_dt = datetime.fromtimestamp(stat_info.st_mtime, tz=timezone.utc)

        with open(filepath, "r", encoding="utf-8") as f:
            plan_data = json.load(f)
        plan_data = _sanitize_plan_dict(plan_data)

        if isinstance(plan_data, dict) and "activity_options" in plan_data:
            sel_title = plan_data.get("selected_activity_title")
            sel_act = plan_data.get("selected_activity")
            opts = plan_data.get("activity_options")
            if isinstance(opts, list) and len(opts) > 1:
                matched = []
                if sel_title:
                    matched = [o for o in opts if isinstance(o, dict) and o.get("title") == sel_title]
                if not matched and sel_act:
                    matched = [o for o in opts if isinstance(o, dict) and (o.get("description") == sel_act or o.get("title") in str(sel_act))]
                plan_data["activity_options"] = matched if matched else [opts[0]]

        plan_id = os.path.splitext(os.path.basename(filepath))[0]
        return {
            "filename": os.path.basename(filepath),
            "id": plan_id,
            "created_at": created_dt.isoformat(),
            "file_size_bytes": stat_info.st_size,
            "plan": plan_data,
        }
    except Exception as exc:
        logger.error("Error reading generated plan %s: %s", filename, exc)
        return None


def get_competency_period_plans(
    grade: str,
    competency_level: str,
    subject: str,
    total_periods: int,
) -> Dict[int, Dict[str, Any]]:
    """Loads saved period plans for one competency sequence, if they exist."""
    grade_part = grade.strip().replace(" ", "_")
    competency_part = competency_level.strip().replace(".", "_")
    plans: Dict[int, Dict[str, Any]] = {}

    for period in range(1, min(max(total_periods, 1), 4) + 1):
        filename = f"{grade_part}_comp_{competency_part}_p{period}.json"
        plan_info = get_generated_plan(filename)
        plan = plan_info.get("plan") if plan_info else None
        if not isinstance(plan, dict):
            continue
        if str(plan.get("grade", "")).strip().lower() != grade.strip().lower():
            continue
        if str(plan.get("subject", "")).strip().lower() != subject.strip().lower():
            continue
        plans[period] = plan

    return plans


def delete_generated_plan(filename: str) -> bool:
    """
    Deletes the target generated plan JSON file safely from the storage directory.
    Returns True if deleted, False if file was not found or failed.
    """
    filepath = _get_safe_filepath(filename)
    if not filepath or not os.path.isfile(filepath):
        logger.warning("Attempted to delete non-existent plan: %s", filename)
        return False

    try:
        os.remove(filepath)
        logger.info("Successfully deleted generated plan file: %s", filepath)
        return True
    except OSError as exc:
        logger.error("Failed to delete plan file %s: %s", filepath, exc)
        raise exc


def save_generated_plan(plan_data: Dict[str, Any], custom_filename: Optional[str] = None) -> str:
    """
    Saves a lesson plan dictionary to the generated_plans directory.
    Returns the saved filename.
    """
    ensure_directory_exists()
    plan_data = _sanitize_plan_dict(plan_data)

    if custom_filename and custom_filename.strip():
        fname = _sanitize_filename(custom_filename)
    else:
        grade = str(plan_data.get("grade", "Grade_8")).strip().replace(" ", "_")
        comp = str(plan_data.get("competence_level", "custom")).strip().replace(".", "_")
        period = plan_data.get("period_number")
        if period is not None:
            fname = f"{grade}_comp_{comp}_p{period}.json"
        else:
            fname = f"{grade}_comp_{comp}.json"

    filepath = _get_safe_filepath(fname)
    if not filepath:
        raise ValueError(f"Invalid target filename: {fname}")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(plan_data, f, indent=2, ensure_ascii=False)

    logger.info("Saved generated plan to: %s", filepath)
    return os.path.basename(filepath)


def find_plan_by_competency(
    competency_level: str,
    grade: Optional[str] = None,
    subject: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Finds a generated lesson plan matching the given competency level, grade, and subject.
    If multiple period plans exist (e.g. p1, p2, p3, p4), sorts them in order,
    returns Period 1 as the primary plan, and attaches all_period_plans.
    """
    clean_comp = competency_level.strip()
    if not clean_comp:
        return None

    plans_dir = ensure_directory_exists()
    try:
        entries = os.listdir(plans_dir)
    except OSError:
        return None

    matching_period_plans: List[Dict[str, Any]] = []
    matching_unsuffixed_plans: List[Dict[str, Any]] = []

    for fname in entries:
        if not fname.lower().endswith(".json"):
            continue
        plan_info = get_generated_plan(fname)
        if not plan_info or not plan_info.get("plan"):
            continue

        p = plan_info["plan"]
        p_comp = str(p.get("competence_level", "")).strip()
        p_grade = str(p.get("grade", "")).strip()
        p_subj = str(p.get("subject", "")).strip()

        if p_comp.lower() == clean_comp.lower():
            if grade and grade.strip().lower() != "all" and grade.strip().lower() != p_grade.lower():
                continue
            if subject and subject.strip().lower() != "all" and subject.strip().lower() != p_subj.lower():
                continue

            period_num = p.get("period_number")
            if period_num is not None and isinstance(period_num, int):
                matching_period_plans.append(plan_info)
            else:
                matching_unsuffixed_plans.append(plan_info)

    if matching_period_plans:
        # Sort period plans strictly by period number (1, 2, 3, 4...)
        matching_period_plans.sort(key=lambda pi: pi["plan"].get("period_number", 0))
        primary = matching_period_plans[0]
        # Attach all period plans so frontend can view every period
        primary["all_period_plans"] = [pi["plan"] for pi in matching_period_plans]
        primary["period_count"] = len(matching_period_plans)
        return primary

    if matching_unsuffixed_plans:
        matching_unsuffixed_plans.sort(key=lambda pi: pi.get("filename", ""))
        primary = matching_unsuffixed_plans[0]
        primary["all_period_plans"] = [pi["plan"] for pi in matching_unsuffixed_plans]
        primary["period_count"] = len(matching_unsuffixed_plans)
        return primary

    return None
