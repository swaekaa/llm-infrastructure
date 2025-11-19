"""
End-to-end pipeline test script.

This script tests the complete Kafka -> LLM -> Results pipeline.
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_service(url: str, name: str, timeout: int = 30) -> bool:
    """Check if a service is responding."""
    print(f"Checking {name} at {url}...", end=" ")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print("✅ OK")
                return True
        except:
            pass
        time.sleep(1)
    
    print("❌ FAILED")
    return False

def check_kafka(broker: str = "localhost:9092") -> bool:
    """Check if Kafka is accessible."""
    print(f"Checking Kafka at {broker}...", end=" ")
    try:
        from kafka import KafkaProducer
        producer = KafkaProducer(
            bootstrap_servers=[broker],
            value_serializer=lambda v: v,
            request_timeout_ms=5000
        )
        producer.close()
        print("✅ OK")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def main():
    """Run pipeline tests."""
    print("=" * 60)
    print("Pipeline Verification Test")
    print("=" * 60)
    
    # Check vLLM
    if not check_service("http://localhost:8000/health", "vLLM Server"):
        print("\n⚠️  vLLM server not responding. Start it with: docker-compose up -d")
        return False
    
    # Check Kafka
    if not check_kafka():
        print("\n⚠️  Kafka not accessible. Start it with: docker-compose up -d")
        return False
    
    print("\n✅ All services are running!")
    print("\nTo test the pipeline:")
    print("1. Start processor: python src/kafka_llm_processor.py")
    print("2. Send test data: python src/test_producer.py --count 1")
    print("3. View results: python src/test_consumer.py --max-messages 1")
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)

