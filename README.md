# LLM Infrastructure

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

Production-ready LLM infrastructure with compliance, privacy, and drift detection. Built for financial services and regulated industries.

## Features

- **Event-Driven Architecture**: Kafka-based streaming with 10k+ req/sec throughput
- **Compliance Ready**: SEC/FINRA/GDPR audit trails with privacy-by-design
- **Drift Detection**: Statistical monitoring using Kolmogorov-Smirnov tests
- **Explainability**: LIME/SHAP integration for model transparency
- **Privacy-First**: PII masking, encryption, multi-tenant isolation
- **Multi-Cloud**: Kubernetes-ready, Apple Silicon optimized

## Quick Start

```bash
# Clone and install
git clone https://github.com/siri1404/llm-infrastructure.git
cd llm-infrastructure
pip install -r requirements.txt

# Start services
docker compose up -d

# Run pipeline
python src/kafka_llm_processor.py
```

## Architecture

```
Producer → Kafka → LLM Processor → Results
                        ↓
                   Audit Logger
                   Drift Detector
                   Explainability
```

**Core Components:**
- `core/compliance/`: Audit logging with PII masking
- `core/drift/`: Statistical drift detection  
- `core/processor/`: Kafka-based LLM processor
- `api/`: FastAPI REST endpoints
- `frontend/`: Next.js monitoring dashboard

## Documentation

- [QUICKSTART.md](QUICKSTART.md) - Get started in 5 minutes
- [KAFKA_SETUP.md](KAFKA_SETUP.md) - Kafka configuration
- [AUDIT_TRAIL_SETUP.md](AUDIT_TRAIL_SETUP.md) - Compliance setup
- [DRIFT_DETECTION_SETUP.md](DRIFT_DETECTION_SETUP.md) - Monitoring setup
- [docs/APPLE_SILICON.md](docs/APPLE_SILICON.md) - Apple Silicon guide

## Dashboard

Start the monitoring dashboard:

```bash
cd frontend
npm install
npm run dev
# Open http://localhost:3000
```

Features real-time metrics, audit logs, drift alerts, and compliance reporting.

## Compliance API

```bash
# Start API server
python src/compliance_api.py

# Query audit logs
curl -X POST http://localhost:5000/api/compliance/query \
  -H "Content-Type: application/json" \
  -d '{"start_time": "2025-01-01T00:00:00Z"}'
```

**Supported Standards**: SEC, FINRA, MiFID II, GDPR

## Benchmarks

Run performance benchmarks:

```bash
python benchmarks/run_benchmarks.py
```

Results (Apple M2 Pro):
- Audit latency: 11.94ms (p99)
- Drift detection: 0.92ms
- Throughput: 900k+ req/sec (batch)

See [benchmarks/README.md](benchmarks/README.md) for details.

## Configuration

Key environment variables:

```bash
# LLM
LLM_URL=http://localhost:11434
MODEL_NAME=llama2

# Kafka
KAFKA_BROKERS=localhost:9092
INPUT_TOPIC=financial-documents

# Audit
ENABLE_AUDIT_LOGGING=true
MASK_SENSITIVE_FIELDS=true
ENCRYPT_AUDIT_DB=false
```

## Deployment

### Docker Compose

```bash
docker compose up -d
```

### Kubernetes

```bash
kubectl apply -f k8s/
```

See deployment guides in `docs/` for AWS, GCP, Azure.

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Priority areas:**
- Additional compliance standards (HIPAA, SOX)
- More LLM backends (Anthropic, Cohere)
- Enhanced privacy features
- Performance optimizations

## License

Apache License 2.0 - see [LICENSE](LICENSE) for details.

## Support

- [GitHub Issues](https://github.com/siri1404/llm-infrastructure/issues)
- [Discussions](https://github.com/siri1404/llm-infrastructure/discussions)
