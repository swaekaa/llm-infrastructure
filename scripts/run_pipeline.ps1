# Run the complete Kafka + LLM pipeline

Write-Host "Starting Kafka + LLM Pipeline..." -ForegroundColor Green

# Check if Docker is running
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

# Start infrastructure (Kafka, Zookeeper, vLLM)
Write-Host "`n1. Starting Docker services (Kafka, Zookeeper, vLLM)..." -ForegroundColor Cyan
docker-compose up -d

Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

# Check if services are up
Write-Host "`n2. Checking service health..." -ForegroundColor Cyan
docker-compose ps

Write-Host "`n3. Installing Python dependencies..." -ForegroundColor Cyan
pip install -r requirements.txt

Write-Host "`n✅ Setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "  - Start processor: python src/kafka_llm_processor.py" -ForegroundColor White
Write-Host "  - Send test data: python src/test_producer.py --count 3" -ForegroundColor White
Write-Host "  - View results: python src/test_consumer.py" -ForegroundColor White
Write-Host "`nTo stop services: docker-compose down" -ForegroundColor Gray

