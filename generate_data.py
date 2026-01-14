import sys
import os
from datetime import datetime, timedelta
import random

sys.path.insert(0, os.path.dirname(__file__) + '/..')
sys.path.insert(0, os.path.dirname(__file__) + '/../src')

from core.compliance.audit_logger import AuditLogger
from core.drift.detector import DriftDetector, DriftMonitor

def main():
    print("=" * 60)
    print("Generating Sample Data for Dashboard")
    print("=" * 60)
    
    audit_logger = AuditLogger()
    drift_detector = DriftDetector()
    monitor = DriftMonitor(drift_detector)  # DriftMonitor requires detector argument
    
    print("\nGenerating 200 audit logs...")
    base_time = datetime.now()
    endpoints = ['/api/v1/completion', '/api/v1/chat', '/api/v1/embedding', '/api/v1/moderation']
    tenants = ['acme-corp', 'finance-ai', 'trading-desk', 'risk-mgmt']
    users = ['alice@company.com', 'bob@finance.com', 'charlie@trading.com', 'diana@risk.com']
    models = ['gpt-4', 'claude-3', 'mixtral', 'llama2']
    
    for i in range(200):
        hours_ago = random.uniform(0, 24)
        timestamp = base_time - timedelta(hours=hours_ago)
        status = 'success' if random.random() > 0.05 else 'error'
        
        input_text = 'Query about financial data: ' + str(i % 50)
        
        model_response = None
        if status == 'success':
            model_response = {
                'choices': [{'text': 'Generated response about financial metrics ' + str(i % 50)}],
                'usage': {
                    'total_tokens': random.randint(50, 1500),
                    'prompt_tokens': random.randint(10, 500),
                    'completion_tokens': random.randint(20, 1000)
                }
            }
        
        metadata = {
            'tenant_id': random.choice(tenants),
            'user_id': random.choice(users),
            'endpoint': random.choice(endpoints),
            'method': 'POST',
            'model_name': random.choice(models),
            'model_version': '1.0',
            'request_id': 'req_' + str(i).zfill(6),
            'timestamp': timestamp.isoformat() + 'Z',
            'processing_time_ms': random.gauss(28, 12),  # Fast latency: 28ms avg, p99 ~52ms
            'status': status,
            'status_code': 200 if status == 'success' else random.choice([400, 429, 500]),
            'model_parameters': {'temperature': 0.7, 'max_tokens': 500}
        }
        
        audit_logger.log_request(input_text, model_response, metadata)
        
        if (i + 1) % 50 == 0:
            print("  Generated " + str(i + 1) + "/200 logs")
    
    print("\nGenerating drift detection data...")
    # Add baseline samples first
    for i in range(100):
        sample = {
            'text': 'Baseline output ' + str(i),
            'tokens_used': random.randint(50, 200),
            'processing_time_ms': random.gauss(28, 12),  # Fast baseline
            'confidence': random.gauss(0.85, 0.05)
        }
        monitor.add_output(sample)
    
    print("  Generated 100 baseline samples")
    
    # Add drifted samples to trigger alerts
    for i in range(80):
        sample = {
            'text': 'Drifted output ' + str(i),
            'tokens_used': random.randint(300, 800),  # Much higher
            'processing_time_ms': random.gauss(85, 25),  # Still fast but slower than baseline
            'confidence': random.gauss(0.65, 0.15)  # Lower confidence
        }
        result = monitor.add_output(sample)
        if result:
            pass  # Drift detected
    
    print("  Generated 80 drifted samples")
    
    stats = audit_logger.get_statistics()
    print("\nAudit Statistics:")
    print("  Total: " + str(stats.get('total_requests', 0)))
    
    print("\n" + "=" * 60)
    print("Data generation complete! Refresh dashboard.")
    print("=" * 60)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print("Error: " + str(e))
        import traceback
        traceback.print_exc()
