from schema import LessonPlanSchema

# Instantiate a sample object to confirm validation passes
sample = LessonPlanSchema(
    title="Introduction to Photosynthesis",
    subject="Grade 8 Science",
    grade_level="Grade 8",
    estimated_duration_minutes=45,
    educational_goal="Understand how plant cells convert light energy into chemical energy.",
    objectives=[
        {
            "id": 1,
            "description": "Identify the primary inputs and outputs of photosynthesis.",
            "blooms_taxonomy_level": "Understand"
        }
    ],
    materials=[
        {
            "item_name": "Diagram of Plant Cell Chloroplast",
            "quantity": "1 per student",
            "is_digital": False
        }
    ],
    procedures=[
        {
            "step_number": 1,
            "phase_title": "Warm-up / Engagement",
            "duration_minutes": 10,
            "teacher_action": "Shows a green leaf and asks students why leaves are green.",
            "student_action": "Brainstorm and write down ideas in notebooks."
        }
    ],
    verification={
        "formative_assessment": "Exit-ticket asking students to write the word equation for photosynthesis.",
        "alignment_check": "Exit-ticket directly evaluates Objective #1."
    }
)

print("✅ Schema created and validated successfully!")
print(f"Lesson Title: {sample.title}")
print(f"Total Steps: {len(sample.procedures)}")