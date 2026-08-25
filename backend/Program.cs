using Microsoft.EntityFrameworkCore;
using ApiGateway.Data;
using ApiGateway.Services;
using Scalar.AspNetCore; // <-- Add Scalar

var builder = WebApplication.CreateBuilder(args);

// 1. MySQL Database Context
var connectionString = builder.Configuration.GetConnectionString("DefaultConnection");
builder.Services.AddDbContext<ApplicationDbContext>(options =>
    options.UseMySql(connectionString, ServerVersion.AutoDetect(connectionString)));

// 2. Controllers & Built-in .NET 9 OpenAPI
builder.Services.AddControllers();
builder.Services.AddOpenApi(); // <-- Standard .NET 9 OpenAPI

// 3. Typed HttpClient for FastAPI
builder.Services.AddHttpClient<ILessonPlanMlService, LessonPlanMlService>(client =>
{
    client.BaseAddress = new Uri(builder.Configuration["MlService:BaseUrl"] ?? "http://127.0.0.1:8000/");
    client.Timeout = TimeSpan.FromSeconds(120);
    client.DefaultRequestHeaders.Add("Accept", "application/json");
});

var app = builder.Build();

// 4. HTTP Pipeline with Scalar Interactive API Docs
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
    app.MapScalarApiReference(); // <-- Interactive UI at /scalar/v1
}

app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

app.Run();