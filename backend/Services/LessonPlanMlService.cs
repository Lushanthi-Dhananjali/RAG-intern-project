using System.Net.Http.Json;
using System.Text.Json;
using ApiGateway.DTOs;

namespace ApiGateway.Services
{
    public class LessonPlanMlService : ILessonPlanMlService
    {
        private readonly HttpClient _httpClient;
        private readonly ILogger<LessonPlanMlService> _logger;

        public LessonPlanMlService(HttpClient httpClient, ILogger<LessonPlanMlService> logger)
        {
            _httpClient = httpClient;
            _logger = logger;
        }

        public async Task<LessonPlanSchemaDto> ExtractCurriculumAsync(
            CurriculumExtractRequest request, 
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Sending raw curriculum text to FastAPI extraction endpoint...");

            var response = await _httpClient.PostAsJsonAsync("api/v1/extract-curriculum", request, cancellationToken);
            
            await EnsureSuccessOrThrowAsync(response);

            var result = await response.Content.ReadFromJsonAsync<LessonPlanSchemaDto>(cancellationToken: cancellationToken);
            return result ?? new LessonPlanSchemaDto();
        }

        public async Task<LessonPlanGenerateResponse> GenerateLessonPlanAsync(
            LessonPlanGenerateRequest request, 
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Sending prompt to FastAPI RAG lesson plan generation endpoint for topic: {Query}", request.Query);

            var response = await _httpClient.PostAsJsonAsync("api/v1/generate-lesson-plan", request, cancellationToken);

            await EnsureSuccessOrThrowAsync(response);

            var result = await response.Content.ReadFromJsonAsync<LessonPlanGenerateResponse>(cancellationToken: cancellationToken);
            return result ?? new LessonPlanGenerateResponse();
        }

        public async Task<AlignmentReportDto> VerifyAlignmentAsync(
            VerifyAlignmentRequest request, 
            CancellationToken cancellationToken = default)
        {
            _logger.LogInformation("Sending alignment verification request to FastAPI...");

            var response = await _httpClient.PostAsJsonAsync("api/v1/verify-alignment", request, cancellationToken);

            await EnsureSuccessOrThrowAsync(response);

            var result = await response.Content.ReadFromJsonAsync<AlignmentReportDto>(cancellationToken: cancellationToken);
            return result ?? new AlignmentReportDto();
        }

        private static async Task EnsureSuccessOrThrowAsync(HttpResponseMessage response)
        {
            if (!response.IsSuccessStatusCode)
            {
                var errorContent = await response.Content.ReadAsStringAsync();
                throw new HttpRequestException(
                    $"FastAPI ML Microservice call failed with status code {(int)response.StatusCode} ({response.ReasonPhrase}): {errorContent}"
                );
            }
        }
    }
}