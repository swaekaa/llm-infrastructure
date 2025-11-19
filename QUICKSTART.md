# Quick Start Guide

## Option 1: Run with Ollama (Recommended - Works on CPU)

### Step 1: Start All Services
```powershell
cd C:\Users\pooja\llm-infrastructure
docker compose up -d
```

This starts:
- Zookeeper
- Kafka  
- Ollama (LLM server)

### Step 2: Pull a Model (First Time Only)
```powershell
# Wait for Ollama to start (~10 seconds)
python scripts/setup_ollama.py --model llama2

# Or use other models:
# python scripts/setup_ollama.py --model mistral
# python scripts/setup_ollama.py --model codellama
```

### Step 3: Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### Step 4: Start the Pipeline
```powershell
# Terminal 1: Start processor
python src/kafka_llm_processor.py

# Terminal 2: Send test data
python src/test_producer.py --count 3

# Terminal 3 (optional): View results
python src/test_consumer.py --max-messages 3
```

**✅ Deliverable Complete:** Real-time Kafka → LLM → Results pipeline working!

---

## Option 2: Run vLLM with Docker (Requires GPU)

### Step 1: Install Docker Desktop
1. Download: https://www.docker.com/products/docker-desktop
2. Install and restart your computer
3. Start Docker Desktop

### Step 2: Start vLLM Server
```powershell
# Using Docker Compose (easiest)
docker-compose up -d

# Or using Docker directly
docker run -d --name vllm-server -p 8000:8000 `
    vllm/vllm-openai:latest `
    --model mistralai/Mistral-7B-Instruct-v0.2 `
    --host 0.0.0.0 `
    --port 8000
```

### Step 3: Test the Server
```powershell
# Install Python dependencies
pip install -r requirements.txt

# Run test script
python src/test_llm.py
```

**✅ Deliverable Complete:** Basic LLM serving working locally!

---

## Option 2: Run vLLM with Kubernetes (Local)

### Step 1: Enable Kubernetes in Docker Desktop
1. Open Docker Desktop
2. Go to Settings → Kubernetes
3. Check "Enable Kubernetes"
4. Click "Apply & Restart"
5. Wait for Kubernetes to start (green icon in bottom bar)

### Step 2: Verify Kubernetes
```powershell
# Install kubectl if not installed
choco install kubernetes-cli

# Verify connection
kubectl get nodes
```

### Step 3: Deploy vLLM to Kubernetes
```powershell
# Deploy vLLM
kubectl apply -f k8s/vllm-deployment.yaml

# Check status
kubectl get pods
kubectl get services

# Port forward to access locally
kubectl port-forward service/vllm-service 8000:80
```

### Step 4: Test
```powershell
# In another terminal
python src/test_llm.py
```

---

## Troubleshooting

### Docker not starting
- Make sure WSL 2 is installed (Windows)
- Restart Docker Desktop

### vLLM container fails
- Check logs: `docker logs vllm-server`
- Try CPU-only mode (remove GPU flags)

### Kubernetes not working
- Make sure Docker Desktop Kubernetes is enabled
- Check: `kubectl cluster-info`

