using System.Text.Json.Serialization;

namespace ApiGateway.DTOs
{
    public class CurriculumExtractRequest
    {
        [JsonPropertyName("raw_text")]
        public string RawText { get; set; } = string.Empty;
    }
}