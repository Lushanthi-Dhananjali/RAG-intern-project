namespace LessonPlanApi.Models
{
    public class ExtractRequestDto
    {
        public string RawText { get; set; } = string.Empty;
    }

    public class LessonObjectiveDto
    {
        public int Id { get; set; }
        public string Description { get; set; } = string.Empty;
        public string? BloomsTaxonomyLevel { get; set; }
    }

    public class MaterialItemDto
    {
        public string ItemName { get; set; } = string.Empty;
        public string Quantity { get; set; } = string.Empty;
        public bool IsDigital { get; set; }
    }

    public class ProcedureStepDto
    {
        public int StepNumber { get; set; }
        public string PhaseTitle { get; set; } = string.Empty;
        public int DurationMinutes { get; set; }
        public string TeacherAction { get; set; } = string.Empty;
        public string StudentAction { get; set; } = string.Empty;
    }

    public class AssessmentAndVerificationDto
    {
        public string FormativeAssessment { get; set; } = string.Empty;
        public string? SummativeAssessment { get; set; }
        public string AlignmentCheck { get; set; } = string.Empty;
    }

    public class LessonPlanResponseDto
    {
        public string Title { get; set; } = string.Empty;
        public string Subject { get; set; } = string.Empty;
        public string GradeLevel { get; set; } = string.Empty;
        public int EstimatedDurationMinutes { get; set; }
        public string EducationalGoal { get; set; } = string.Empty;
        public List<LessonObjectiveDto> Objectives { get; set; } = new();
        public List<MaterialItemDto> Materials { get; set; } = new();
        public List<ProcedureStepDto> Procedures { get; set; } = new();
        public AssessmentAndVerificationDto Verification { get; set; } = new();
    }
}