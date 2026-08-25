namespace ApiGateway.Entities
{
    public class SavedLessonPlan
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public Guid UserId { get; set; }
        public string Title { get; set; } = string.Empty;
        public string GradeLevel { get; set; } = string.Empty;
        public string Topic { get; set; } = string.Empty;
        
        // Stores full structured LessonPlanSchema JSON payload
        public string PlanJsonData { get; set; } = string.Empty; 

        public DateTime SavedAt { get; set; } = DateTime.UtcNow;

        // Navigation Property
        public User? User { get; set; }
    }
}