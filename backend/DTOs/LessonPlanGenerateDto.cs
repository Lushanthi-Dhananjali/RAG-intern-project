using System.Text.Json.Serialization;

namespace ApiGateway.DTOs
{
    public class LessonPlanGenerateRequest
    {
        [JsonPropertyName("query")]
        public string Query { get; set; } = string.Empty;

        [JsonPropertyName("grade_level")]
        public string GradeLevel { get; set; } = "Grade 9";
    }

    public class LessonPlanGenerateResponse
    {
        [JsonPropertyName("lesson_plan")]
        public LessonPlanSchemaDto LessonPlan { get; set; } = new();

        [JsonPropertyName("fact_check_report")]
        public FactCheckReportDto? FactCheckReport { get; set; }

        [JsonPropertyName("alignment_report")]
        public AlignmentReportDto? AlignmentReport { get; set; }
    }
}