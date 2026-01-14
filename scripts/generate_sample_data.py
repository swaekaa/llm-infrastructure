"""
Generate sample audit log and drift data for dashboard visualization.
This populates the database with realistic data for the UI to display.
"""

import sys
import os
from datetime import datetime, timedelta
import random
import json

# Add paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.compliance.audit_logger import AuditLogger
from core.drift.detector import DriftDetector, DriftMonitor


def generate_sample_audit_logs():
    """Generate sample audit logs for the dashboard."""
    
    audit_logger = AuditLogger()
    
    # Generate 200 logs over the last 24 hours
    base_time = datetime.now()
    
    endpoints = [
        '/api/v1/completion',
        '/api/v1/chat',
        '/api/v1/embedding',
        '/api/v1/moderation'
    ]
    
    tenants = ['acme-corp', 'finance-ai', 'trading-desk', 'risk-mgmt']
    users = ['alice@company.com', 'bob@finance.com', 'charlie@trading.com', 'diana@risk.com']
    models = ['gpt-4', 'claude-3', 'mixtral', 'llama2']
    
    print("Generating sample audit logs...")
    
    for i in range(200):
        # Spread logs over 24 hours
        hours_ago = random.uniform(0, 24)
        timestamp = base_time - timedelta(hours=hours_ago)
        
        # 95% success rate, 5% errors
        status = 'success' if random.random() > 0.05 else 'error'
        
        log_entry = {
            'tenant_id': random.choice(tenants),
            'user_id': random.choice(users),
            'endpoint': random.choice(endpoints),
            'method': 'POST',
            'model': random.choice(models),
            'input_tokens': random.randint(10, 500),
            'output_tokens': random.randint(20, 1000),
            'total_tokens': random.randint(30, 1500),
            'processing_time_ms': random.gauss(250, 50),  # Normal distribution
            'status': status,
            'status_code': 200 if status == 'success' else random.choice([400, 429, 500]),
            'error_message': None if status == 'success' else random.choice([
                'Rate limit exceeded',
                'Invalid input',
                'Service temporarily unavailable'
            ]),
            'model_version': '1.0',
            'request_id': f"req_{i:06d}",
            'prompt_summary': f"Query about financial data {i % 50}",
            'response_summary': f"Generated response {i % 50}",
        }
        
        # Add some random metadata
        log_entry['metadata'] = {
            'client_ip': f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}",
            'user_agent': random.choice([
                'Python/3.10 requests',
                'Node.js/18 axios',
                'cURL/7.85',
                'Java/11 OkHttp'
            ]),
            'region': random.choice(['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1'])
        }
        
        # Log the entry
        audit_logger.log_request(log_entry)
        
        if (i + 1) % 50 == 0:
            print(f"  Generated {i + 1}/200 logs")
    
    print(f"✅ Generated 200 audit logs")
    
    # Get statistics
    stats = audit_logger.get_statistics()
    print(f"\nAudit Log Statistics:")
    print(f"  Total requests: {stats.get('total_requests', 0)}")
    print(f"  Success: {stats.get('by_status', {}).get('success', 0)}")
    print(f"  Errors: {stats.get('by_status', {}).get('error', 0)}")
    print(f"  Avg processing time: {stats.get('avg_processing_time_ms', 0):.2f}ms")
    

def generate_sample_drift_data():
    """Generate sample drift detection data."""
    
    drift_detector = DriftDetector()
    monitor = DriftMonitor()
    
    print("\nGenerating sample drift detection data...")
    
    # Generate baseline samples (normal distribution)
    baseline_samples = []
    for i in range(100):
        sample = {
            'text_length': random.gauss(300, 50),
            'token_count': random.gauss(75, 15),
            'processing_time_ms': random.gauss(200, 40),
            'has_currency': random.choice([0, 1]),
            'has_date': random.choice([0, 1]),
            'sentiment_score': random.gauss(0.5, 0.2),
            'complexity_score': random.gauss(0.6, 0.15)
        }
        baseline_samples.append(sample)
    
    # Establish baseline
    drift_detector.establish_baseline(baseline_samples)
    print(f"  Established baseline with 100 samples")
    
    # Generate normal samples (within baseline distribution)
    print("  Generating 50 normal samples...")
    normal_samples = []
    for i in range(50):
        sample = {
            'text_length': random.gauss(300, 50),
            'token_count': random.gauss(75, 15),
            'processing_time_ms': random.gauss(200, 40),
            'has_currency': random.choice([0, 1]),
            'has_date': random.choice([0, 1]),
            'sentiment_score': random.gauss(0.5, 0.2),
            'complexity_score': random.gauss(0.6, 0.15)
        }
        normal_samples.append(sample)
        
        # Check for drift
        result = drift_detector.detect_drift(sample)
        monitor.record_check(result)
    
    # Generate drifted samples (outside baseline distribution)
    print("  Generating 30 drifted samples...")
    drifted_samples = []
    for i in range(30):
        sample = {
            'text_length': random.gauss(600, 100),  # Much longer
            'token_count': random.gauss(150, 30),   # More tokens
            'processing_time_ms': random.gauss(400, 80),  # Slower
            'has_currency': 1,  # More financial
            'has_date': 1,
            'sentiment_score': random.gauss(0.2, 0.3),  # More negative
            'complexity_score': random.gauss(0.9, 0.1)  # More complex
        }
        drifted_samples.append(sample)
        
        # Check for drift
        result = drift_detector.detect_drift(sample)
        monitor.record_check(result)
    
    # Get statistics
    stats = monitor.get_statistics()
    print(f"\n✅ Generated 80 drift detection samples")
    print(f"\nDrift Detection Statistics:")
    print(f"  Total checks: {stats.get('total_checks', 0)}")
    print(f"  Drift detected: {stats.get('drift_detected_count', 0)}")
    print(f"  Detection rate: {stats.get('drift_detection_rate', 0):.2f}%")
    print(f"  Avg detection latency: {stats.get('avg_detection_latency_ms', 0):.2f}ms")


if __name__ == '__main__':
    print("=" * 60)
    print("Generating Sample Data for Dashboard")
    print("=" * 60)
    
    try:
        generate_sample_audit_logs()
        generate_sample_drift_data()
        
        print("\n" + "=" * 60)
        print("✅ Sample data generation complete!")
        print("=" * 60)
        print("\nRefresh your Streamlit dashboard to see the data.")
        
    except Exception as e:
        print(f"❌ Error generating sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
