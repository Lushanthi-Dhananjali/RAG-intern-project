using ApiGateway.DTOs;

namespace ApiGateway.Services
{
    public interface ILessonPlanMlService
    {
        Task<LessonPlanSchemaDto> ExtractCurriculumAsync(CurriculumExtractRequest request, CancellationToken cancellationToken = default);
        Task<LessonPlanGenerateResponse> GenerateLessonPlanAsync(LessonPlanGenerateRequest request, CancellationToken cancellationToken = default);
        Task<AlignmentReportDto> VerifyAlignmentAsync(VerifyAlignmentRequest request, CancellationToken cancellationToken = default);
    }
}