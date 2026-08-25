namespace ApiGateway.Entities
{
    public class GenerationHistory
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public Guid UserId { get; set; }
        public string QueryPrompt { get; set; } = string.Empty;
        public double GroundingScore { get; set; }
        public double AlignmentScore { get; set; }
        public DateTime ExecutedAt { get; set; } = DateTime.UtcNow;

        // Navigation Property
        public User? User { get; set; }
    }
}