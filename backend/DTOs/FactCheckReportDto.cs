using System.Text.Json.Serialization;

namespace ApiGateway.DTOs
{
    public class FactCheckReportDto
    {
        [JsonPropertyName("total_claims_extracted")]
        public int TotalClaimsExtracted { get; set; }

        [JsonPropertyName("supported_claims_count")]
        public int SupportedClaimsCount { get; set; }

        [JsonPropertyName("grounding_score")]
        public double GroundingScore { get; set; }

        [JsonPropertyName("passed")]
        public bool Passed { get; set; }

        [JsonPropertyName("unsupported_claims")]
        public List<string> UnsupportedClaims { get; set; } = new();

        [JsonPropertyName("explanation")]
        public string Explanation { get; set; } = string.Empty;
    }
}