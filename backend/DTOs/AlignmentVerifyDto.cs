using System.Text.Json.Serialization;

namespace ApiGateway.DTOs
{
    public class VerifyAlignmentRequest
    {
        [JsonPropertyName("educational_goal")]
        public string EducationalGoal { get; set; } = string.Empty;

        [JsonPropertyName("lesson_objectives")]
        public List<string> LessonObjectives { get; set; } = new();
    }
}