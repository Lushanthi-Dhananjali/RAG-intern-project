using System.Text.Json.Serialization;

namespace ApiGateway.DTOs
{
    public class LessonPlanSchemaDto
    {
        [JsonPropertyName("title")]
        public string Title { get; set; } = string.Empty;

        [JsonPropertyName("subject")]
        public string Subject { get; set; } = "Civic Education";

        [JsonPropertyName("grade_level")]
        public string GradeLevel { get; set; } = string.Empty;

        [JsonPropertyName("topic")]
        public string Topic { get; set; } = string.Empty;

        [JsonPropertyName("educational_goal_or_standard")]
        public string EducationalGoalOrStandard { get; set; } = string.Empty;

        [JsonPropertyName("estimated_duration_minutes")]
        public int EstimatedDurationMinutes { get; set; } = 45;

        [JsonPropertyName("learning_outcomes")]
        public List<LearningOutcomeDto> LearningOutcomes { get; set; } = new();

        [JsonPropertyName("materials")]
        public List<MaterialItemDto> Materials { get; set; } = new();

        [JsonPropertyName("procedures")]
        public List<ProcedureStepDto> Procedures { get; set; } = new();

        [JsonPropertyName("verification")]
        public AssessmentAndVerificationDto Verification { get; set; } = new();
    }

    public class LearningOutcomeDto
    {
        [JsonPropertyName("id")]
        public int Id { get; set; }

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("blooms_taxonomy_level")]
        public string? BloomsTaxonomyLevel { get; set; }
    }

    public class MaterialItemDto
    {
        [JsonPropertyName("item_name")]
        public string ItemName { get; set; } = string.Empty;

        [JsonPropertyName("quantity")]
        public string Quantity { get; set; } = string.Empty;

        [JsonPropertyName("is_digital")]
        public bool IsDigital { get; set; } = false;
    }

    public class ProcedureStepDto
    {
        [JsonPropertyName("step_number")]
        public int StepNumber { get; set; }

        [JsonPropertyName("phase_title")]
        public string PhaseTitle { get; set; } = string.Empty;

        [JsonPropertyName("duration_minutes")]
        public int DurationMinutes { get; set; }

        [JsonPropertyName("teacher_action")]
        public string TeacherAction { get; set; } = string.Empty;

        [JsonPropertyName("student_action")]
        public string StudentAction { get; set; } = string.Empty;
    }

    public class AssessmentAndVerificationDto
    {
        [JsonPropertyName("formative_assessment")]
        public string FormativeAssessment { get; set; } = string.Empty;

        [JsonPropertyName("summative_assessment")]
        public string? SummativeAssessment { get; set; }

        [JsonPropertyName("alignment_check")]
        public string AlignmentCheck { get; set; } = string.Empty;
    }
}