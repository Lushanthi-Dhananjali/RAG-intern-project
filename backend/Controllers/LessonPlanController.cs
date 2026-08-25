using Microsoft.AspNetCore.Mvc;
using Microsoft.EntityFrameworkCore;
using ApiGateway.Data;
using ApiGateway.DTOs;
using ApiGateway.Entities;
using ApiGateway.Services;

namespace ApiGateway.Controllers
{
    [ApiController]
    [Route("api/v1/[controller]")]
    public class LessonPlanController : ControllerBase
    {
        private readonly ILessonPlanMlService _mlService;
        private readonly ApplicationDbContext _dbContext;
        private readonly IHttpClientFactory _httpClientFactory;
        private readonly ILogger<LessonPlanController> _logger;

        public LessonPlanController(
            ILessonPlanMlService mlService, 
            ApplicationDbContext dbContext,
            IHttpClientFactory httpClientFactory,
            ILogger<LessonPlanController> logger)
        {
            _mlService = mlService;
            _dbContext = dbContext;
            _httpClientFactory = httpClientFactory;
            _logger = logger;
        }

        /// <summary>
        /// POST /api/v1/lessonplan/generate
        /// Generates a structured lesson plan via FastAPI RAG and logs execution metrics in MySQL.
        /// </summary>
        [HttpPost("generate")]
        public async Task<ActionResult<LessonPlanGenerateResponse>> GenerateLessonPlan(
            [FromBody] LessonPlanGenerateRequest request,
            [FromQuery] Guid? userId,
            CancellationToken cancellationToken)
        {
            if (string.IsNullOrWhiteSpace(request.Query))
            {
                return BadRequest("Query prompt cannot be empty.");
            }

            try
            {
                // 1. Call FastAPI ML Microservice via Typed HttpClient
                var mlResponse = await _mlService.GenerateLessonPlanAsync(request, cancellationToken);

                // 2. Persist Generation Metrics to MySQL Database if userId is provided
                if (userId.HasValue)
                {
                    var userExists = await _dbContext.Users.AnyAsync(u => u.Id == userId.Value, cancellationToken);
                    if (userExists)
                    {
                        var historyLog = new GenerationHistory
                        {
                            UserId = userId.Value,
                            QueryPrompt = request.Query,
                            GroundingScore = mlResponse.FactCheckReport?.GroundingScore ?? 0.0,
                            AlignmentScore = mlResponse.AlignmentReport?.OverallAlignmentScore ?? 0.0,
                            ExecutedAt = DateTime.UtcNow
                        };

                        _dbContext.GenerationHistory.Add(historyLog);
                        await _dbContext.SaveChangesAsync(cancellationToken);
                    }
                }

                return Ok(mlResponse);
            }
            catch (HttpRequestException ex)
            {
                _logger.LogError(ex, "Communication error with FastAPI ML microservice.");
                return StatusCode(503, "The AI ML microservice is currently unreachable. Please check if FastAPI is running.");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Unexpected error during lesson plan generation.");
                return StatusCode(500, $"Internal server error: {ex.Message}");
            }
        }

        /// <summary>
        /// POST /api/v1/lessonplan/generate-stream
        /// Streams tokenized lesson plan output in real-time using Server-Sent Events (SSE).
        /// </summary>
        [HttpPost("generate-stream")]
        public async Task StreamLessonPlan(
            [FromBody] LessonPlanGenerateRequest request,
            CancellationToken cancellationToken)
        {
            if (string.IsNullOrWhiteSpace(request.Query))
            {
                Response.StatusCode = 400;
                await Response.WriteAsync("Query prompt cannot be empty.", cancellationToken);
                return;
            }

            // Set Server-Sent Events (SSE) headers
            Response.Headers.Append("Content-Type", "text/event-stream");
            Response.Headers.Append("Cache-Control", "no-cache");
            Response.Headers.Append("Connection", "keep-alive");

            try
            {
                var client = _httpClientFactory.CreateClient();
                client.Timeout = TimeSpan.FromMinutes(5); // Allow extended timeout for streaming RAG generation

                using var httpRequest = new HttpRequestMessage(HttpMethod.Post, "http://127.0.0.1:8000/api/v1/generate-lesson-plan-stream")
                {
                    Content = JsonContent.Create(request)
                };

                using var response = await client.SendAsync(httpRequest, HttpCompletionOption.ResponseHeadersRead, cancellationToken);

                if (!response.IsSuccessStatusCode)
                {
                    await Response.WriteAsync($"data: [ERROR] Python ML service returned status code {response.StatusCode}\n\n", cancellationToken);
                    await Response.Body.FlushAsync(cancellationToken);
                    return;
                }

                using var stream = await response.Content.ReadAsStreamAsync(cancellationToken);
                using var reader = new StreamReader(stream);

                while (!reader.EndOfStream && !cancellationToken.IsCancellationRequested)
                {
                    var line = await reader.ReadLineAsync(cancellationToken);
                    if (!string.IsNullOrWhiteSpace(line))
                    {
                        // Pass along stream token chunks to the client
                        if (line.StartsWith("data: "))
                        {
                            await Response.WriteAsync($"{line}\n\n", cancellationToken);
                        }
                        else
                        {
                            await Response.WriteAsync($"data: {line}\n\n", cancellationToken);
                        }
                        
                        await Response.Body.FlushAsync(cancellationToken);
                    }
                }
            }
            catch (TaskCanceledException)
            {
                _logger.LogInformation("Streaming request was cancelled by the client.");
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error occurred during streaming lesson plan execution.");
                await Response.WriteAsync($"data: [ERROR] {ex.Message}\n\n", cancellationToken);
                await Response.Body.FlushAsync(cancellationToken);
            }
        }
    }
}