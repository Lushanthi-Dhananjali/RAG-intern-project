using System.Text.Json.Serialization;

namespace ApiGateway.DTOs
{
    public class AlignmentReportDto
    {
        [JsonPropertyName("educational_goal")]
        public string EducationalGoal { get; set; } = string.Empty;

        [JsonPropertyName("overall_alignment_score")]
        public double OverallAlignmentScore { get; set; }

        [JsonPropertyName("passed_alignment_guardrail")]
        public bool PassedAlignmentGuardrail { get; set; }

        [JsonPropertyName("detailed_objectives_alignment")]
        public List<ObjectiveAlignmentDetailDto> DetailedObjectivesAlignment { get; set; } = new();
    }

    public class ObjectiveAlignmentDetailDto
    {
        [JsonPropertyName("objective_id")]
        public int ObjectiveId { get; set; }

        [JsonPropertyName("objective_text")]
        public string ObjectiveText { get; set; } = string.Empty;

        [JsonPropertyName("semantic_similarity_score")]
        public double SemanticSimilarityScore { get; set; }

        [JsonPropertyName("pedagogical_alignment_score")]
        public double PedagogicalAlignmentScore { get; set; }

        [JsonPropertyName("is_aligned")]
        public bool IsAligned { get; set; }

        [JsonPropertyName("alignment_reasoning")]
        public string AlignmentReasoning { get; set; } = string.Empty;
    }
}