using Microsoft.AspNetCore.Mvc;
using System.Text;
using System.Text.Json;
using LessonPlanApi.Models;

namespace LessonPlanApi.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    public class LessonPlanController : ControllerBase
    {
        private readonly IHttpClientFactory _httpClientFactory;

        public LessonPlanController(IHttpClientFactory httpClientFactory)
        {
            _httpClientFactory = httpClientFactory;
        }

        [HttpPost("extract")]
        public async Task<IActionResult> ExtractLessonPlan([FromBody] ExtractRequestDto request)
        {
            if (string.IsNullOrWhiteSpace(request.RawText))
            {
                return BadRequest("Raw text is required.");
            }

            // 1. Create client to call local Python FastAPI service
            var client = _httpClientFactory.CreateClient();

            var jsonPayload = JsonSerializer.Serialize(new { raw_text = request.RawText });
            var httpContent = new StringContent(jsonPayload, Encoding.UTF8, "application/json");

            // 2. Call Python FastAPI microservice
            var response = await client.PostAsync("http://127.0.0.1:8000/api/v1/extract", httpContent);

            if (!response.IsSuccessStatusCode)
            {
                var errorMsg = await response.Content.ReadAsStringAsync();
                return StatusCode((int)response.StatusCode, $"Python Service Error: {errorMsg}");
            }

            // 3. Deserialize Python JSON response into C# DTO
            var responseStream = await response.Content.ReadAsStreamAsync();
            var options = new JsonSerializerOptions { PropertyNameCaseInsensitive = true };
            var result = await JsonSerializer.DeserializeAsync<LessonPlanResponseDto>(responseStream, options);

            // 4. Return clean response to frontend client
            return Ok(result);
        }
    }
}