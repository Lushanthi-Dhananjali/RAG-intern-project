namespace ApiGateway.Entities
{
    public class User
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public string Email { get; set; } = string.Empty;
        public string PasswordHash { get; set; } = string.Empty;
        public string FullName { get; set; } = string.Empty;
        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

        // Navigation Properties
        public ICollection<SavedLessonPlan> SavedLessonPlans { get; set; } = new List<SavedLessonPlan>();
        public ICollection<GenerationHistory> HistoryLogs { get; set; } = new List<GenerationHistory>();
    }
}