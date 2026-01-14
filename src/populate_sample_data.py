"""
Populate sample data for testing the dashboard.
"""

import sys
import os
import random
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit_logger import AuditLogger
from drift_detector import DriftMonitor

def populate_audit_logs():
    """Add sample audit logs."""
    print("Populating audit logs...")
    
    audit_logger = AuditLogger(db_path='audit_logs.db')
    
    models = ['gpt-4', 'gpt-3.5-turbo', 'claude-2']
    sources = ['web-app', 'api', 'mobile-app']
    statuses = ['success'] * 9 + ['error']  # 90% success rate
    
    # Generate 200 sample logs over the last 24 hours
    base_time = datetime.now()
    
    for i in range(200):
        time_offset = timedelta(hours=random.randint(0, 24))
        timestamp = (base_time - time_offset).isoformat()
        
        model = random.choice(models)
        source = random.choice(sources)
        status = random.choice(statuses)
        
        model_response = {
            'model': model,
            'usage': {
                'prompt_tokens': random.randint(50, 500),
                'completion_tokens': random.randint(20, 200),
                'total_tokens': random.randint(70, 700)
            },
            'processing_time_ms': random.randint(100, 2000)
        } if status == 'success' else None
        
        audit_logger.log_request(
            input_text=f"Sample query {i}",
            model_response=model_response,
            metadata={
                'model_version': model,
                'request_id': f"req_{i}",
                'user_id': f"user_{random.randint(1, 10)}",
                'tenant_id': f"tenant_{random.randint(1, 5)}",
                'source': source,
                'test': True,
                'timestamp': timestamp
            }
        )
    
    print(f"✓ Created 200 audit log entries")
    
    # Verify
    stats = audit_logger.get_statistics()
    print(f"  Total requests: {stats.get('total_requests', 0)}")
    print(f"  Success: {stats.get('by_status', {}).get('success', 0)}")
    print(f"  Errors: {stats.get('by_status', {}).get('error', 0)}")


def populate_drift_alerts():
    """Add sample drift alerts."""
    print("\nPopulating drift alerts...")
    
    # Don't need DriftMonitor - just insert directly into database
    import sqlite3
    
    # Generate 247 sample drift alerts
    base_time = datetime.now()
    
    alert_types = ['latency', 'token_usage', 'response_length', 'error_rate']
    
    conn = sqlite3.connect('drift_alerts.db')
    cursor = conn.cursor()
    
    for i in range(247):
        time_offset = timedelta(hours=random.randint(0, 168))  # Last 7 days
        timestamp = (base_time - time_offset).isoformat()
        
        alert_type = random.choice(alert_types)
        
        cursor.execute('''
            INSERT INTO drift_alerts (
                timestamp, drift_score, drifted_features,
                baseline_samples, recent_samples, details, acknowledged
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            random.uniform(0.05, 0.95),
            alert_type,
            random.randint(100, 1000),
            random.randint(50, 500),
            f"Drift detected in {alert_type}",
            random.choice([0, 0, 0, 1])  # 75% unacknowledged
        ))
    
    conn.commit()
    conn.close()
    
    print(f"✓ Created 247 drift alert entries")


if __name__ == '__main__':
    print("=" * 60)
    print("Populating Sample Data")
    print("=" * 60)
    
    populate_audit_logs()
    populate_drift_alerts()
    
    print("\n" + "=" * 60)
    print("✅ Sample data populated successfully!")
    print("=" * 60)
    print("\nRefresh your dashboard to see the data.")
