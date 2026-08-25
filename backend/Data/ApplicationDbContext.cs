using Microsoft.EntityFrameworkCore;
using ApiGateway.Entities;

namespace ApiGateway.Data
{
    public class ApplicationDbContext : DbContext
    {
        public ApplicationDbContext(DbContextOptions<ApplicationDbContext> options) : base(options) { }

        public DbSet<User> Users => Set<User>();
        public DbSet<SavedLessonPlan> SavedLessonPlans => Set<SavedLessonPlan>();
        public DbSet<GenerationHistory> GenerationHistory => Set<GenerationHistory>();

        protected override void OnModelCreating(ModelBuilder modelBuilder)
        {
            base.OnModelCreating(modelBuilder);

            modelBuilder.Entity<User>()
                .HasIndex(u => u.Email)
                .IsUnique();

            modelBuilder.Entity<SavedLessonPlan>()
                .HasOne(p => p.User)
                .WithMany(u => u.SavedLessonPlans)
                .HasForeignKey(p => p.UserId);

            modelBuilder.Entity<GenerationHistory>()
                .HasOne(h => h.User)
                .WithMany(u => u.HistoryLogs)
                .HasForeignKey(h => h.UserId);
        }
    }
}