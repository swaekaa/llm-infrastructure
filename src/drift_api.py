"""
Drift Detection API for monitoring LLM performance.

Provides REST API for querying drift alerts and statistics.
"""

import logging
import os
import sys
import time
import json
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
from typing import Dict

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from drift_detector import DriftMonitor, DriftDetector
    DRIFT_DETECTION_AVAILABLE = True
except ImportError as e:
    logger = logging.getLogger(__name__)
    logger.error(f"Failed to import drift_detector: {e}")
    DRIFT_DETECTION_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": ["http://localhost:3000", "http://localhost:8501"]}})  # Enable CORS for frontend

# Initialize drift monitor (read-only for API)
drift_monitor = None
if DRIFT_DETECTION_AVAILABLE:
    try:
        detector = DriftDetector()
        db_path = os.getenv('DRIFT_DB_PATH', 'drift_alerts.db')
        drift_monitor = DriftMonitor(detector=detector, db_path=db_path)
    except Exception as e:
        logger.warning(f"Failed to initialize drift monitor: {e}")


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "service": "drift-detection-api",
        "drift_detection_available": DRIFT_DETECTION_AVAILABLE
    }), 200


@app.route('/api/drift/alerts', methods=['GET'])
def get_alerts():
    """
    Get drift alerts.
    
    Query parameters:
        limit: Maximum number of alerts (default: 100)
        start_time: ISO format start time
        end_time: ISO format end time
    """
    if not drift_monitor:
        return jsonify({"error": "Drift detection not available"}), 503
    
    try:
        import sqlite3
        db_path = os.getenv('DRIFT_DB_PATH', 'drift_alerts.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        query = "SELECT * FROM drift_alerts WHERE 1=1"
        params = []
        
        start_time = request.args.get('start_time')
        end_time = request.args.get('end_time')
        
        if start_time:
            query += " AND timestamp >= ?"
            params.append(start_time)
        
        if end_time:
            query += " AND timestamp <= ?"
            params.append(end_time)
        
        limit = int(request.args.get('limit', 100))
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        alerts = [dict(row) for row in rows]
        conn.close()
        
        return jsonify(alerts), 200
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/drift/statistics', methods=['GET'])
def get_statistics():
    """Get drift detection statistics."""
    if not drift_monitor:
        return jsonify({"error": "Drift detection not available"}), 503
    
    try:
        import sqlite3
        db_path = os.getenv('DRIFT_DB_PATH', 'drift_alerts.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get total alerts
        cursor.execute("SELECT COUNT(*) FROM drift_alerts")
        total_alerts = cursor.fetchone()[0]
        
        # Get unacknowledged alerts
        cursor.execute("SELECT COUNT(*) FROM drift_alerts WHERE acknowledged = 0")
        unacknowledged = cursor.fetchone()[0]
        
        # Get baseline status from detector
        stats = drift_monitor.detector.get_statistics()
        
        stats['total_alerts'] = total_alerts
        stats['unacknowledged_alerts'] = unacknowledged
        stats['acknowledged_alerts'] = total_alerts - unacknowledged
        stats['drift_alerts'] = total_alerts  # Alias for compatibility
        
        # Get last drift check
        cursor.execute("SELECT MAX(timestamp) FROM drift_alerts")
        last_check = cursor.fetchone()[0]
        stats['last_drift_check'] = last_check
        
        # Calculate average drift score if there are alerts
        if total_alerts > 0:
            cursor.execute("SELECT AVG(drift_score) FROM drift_alerts")
            avg_score = cursor.fetchone()[0]
            stats['avg_drift_score'] = round(avg_score, 2) if avg_score else 0
        else:
            stats['avg_drift_score'] = 0
        
        conn.close()
        
        return jsonify(stats), 200
        
    except Exception as e:
        logger.error(f"Error getting statistics: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/drift/alert/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id: int):
    """Acknowledge a drift alert."""
    if not drift_monitor:
        return jsonify({"error": "Drift detection not available"}), 503
    
    try:
        drift_monitor.acknowledge_alert(alert_id)
        return jsonify({"message": "Alert acknowledged", "alert_id": alert_id}), 200
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/drift/reset-baseline', methods=['POST'])
def reset_baseline():
    """
    Reset baseline distribution with recent outputs.
    
    This should be called after model updates or when you want to recalibrate.
    """
    if not drift_monitor:
        return jsonify({"error": "Drift detection not available"}), 503
    
    try:
        drift_monitor.detector.reset_baseline()
        return jsonify({"message": "Baseline reset successfully"}), 200
    except Exception as e:
        logger.error(f"Error resetting baseline: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@app.route('/api/drift/stream', methods=['GET'])
def stream_drift_updates():
    """
    Server-Sent Events endpoint for real-time drift updates.
    Streams drift statistics and recent alerts every 2 seconds.
    """
    def generate():
        last_alert_count = 0
        while True:
            try:
                import sqlite3
                db_path = os.getenv('DRIFT_DB_PATH', 'drift_alerts.db')
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get statistics
                cursor.execute("""
                    SELECT COUNT(*) as total_alerts,
                           SUM(CASE WHEN acknowledged = 0 THEN 1 ELSE 0 END) as unacknowledged,
                           AVG(drift_score) as avg_drift_score
                    FROM drift_alerts
                """)
                stats_row = cursor.fetchone()
                
                # Get recent alerts
                cursor.execute("""
                    SELECT id, timestamp, drifted_features, drift_score, 
                           baseline_samples, recent_samples, acknowledged
                    FROM drift_alerts
                    ORDER BY timestamp DESC
                    LIMIT 5
                """)
                recent_alerts = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                stats = {
                    'total_alerts': stats_row['total_alerts'] or 0,
                    'unacknowledged_alerts': stats_row['unacknowledged'] or 0,
                    'avg_drift_score': float(stats_row['avg_drift_score']) if stats_row['avg_drift_score'] else 0.0,
                    'recent_alerts': recent_alerts
                }
                
                current_count = stats['total_alerts']
                
                # Only send if data changed
                if current_count != last_alert_count:
                    data = json.dumps(stats)
                    yield f"data: {data}\n\n"
                    last_alert_count = current_count
                else:
                    # Send heartbeat
                    yield f": heartbeat\n\n"
                
                time.sleep(2)
            except Exception as e:
                logger.error(f"Error in SSE stream: {e}")
                yield f"data: {{\"error\": \"Stream error\"}}\n\n"
                time.sleep(5)
    
    return Response(stream_with_context(generate()), 
                    mimetype='text/event-stream',
                    headers={
                        'Cache-Control': 'no-cache',
                        'X-Accel-Buffering': 'no',
                        'Connection': 'keep-alive'
                    })


if __name__ == '__main__':
    port = int(os.getenv('DRIFT_API_PORT', 5001))
    host = os.getenv('DRIFT_API_HOST', '0.0.0.0')
    
    logger.info(f"Starting Drift Detection API on {host}:{port}")
    logger.info("Endpoints:")
    logger.info("  GET  /api/drift/alerts - Get drift alerts")
    logger.info("  GET  /api/drift/statistics - Get statistics")
    logger.info("  POST /api/drift/alert/<id>/acknowledge - Acknowledge alert")
    logger.info("  POST /api/drift/reset-baseline - Reset baseline")
    logger.info("  GET  /api/drift/stream - SSE real-time updates")
    
    app.run(host=host, port=port, debug=False, threaded=True)

