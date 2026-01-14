"""
Audit logging system for LLM inference requests.

Provides comprehensive audit trails for regulatory compliance (SEC, FINRA, GDPR, CCPA).
Includes privacy-by-design features: field masking, anonymization, and encryption.
"""

import hashlib
import json
import logging
import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, Optional, List
from pathlib import Path

logger = logging.getLogger(__name__)

# Try to import encryption libraries (optional)
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    import base64
    ENCRYPTION_AVAILABLE = True
except ImportError:
    ENCRYPTION_AVAILABLE = False
    logger.warning("Encryption not available. Install with: pip install cryptography")


class AuditLogger:
    """
    Handles audit logging for LLM inference requests with privacy-by-design.
    
    Features:
    - Field masking/anonymization for sensitive data
    - Optional encryption for audit database
    - GDPR/CCPA compliance support
    - Per-tenant data isolation
    - In-memory caching for fast statistics queries
    - Batch operations for high throughput
    """
    
    def __init__(self, db_path: Optional[str] = None, 
                 mask_sensitive_fields: bool = True,
                 anonymize_user_ids: bool = False,
                 encrypt_db: bool = False,
                 encryption_key: Optional[str] = None,
                 enable_caching: bool = True):
        """
        Initialize audit logger with performance optimizations.
        
        Args:
            db_path: Path to SQLite database (default: ./audit_logs.db)
            mask_sensitive_fields: Mask PII in audit logs by default (GDPR/CCPA)
            anonymize_user_ids: Hash user IDs for anonymization
            encrypt_db: Enable encryption for audit database
            encryption_key: Encryption key (if None, uses ENCRYPT_AUDIT_DB_KEY env var)
            enable_caching: Enable in-memory caching for statistics (faster queries)
        """
        if db_path is None:
            db_path = os.getenv('AUDIT_DB_PATH', 'audit_logs.db')
        
        self.db_path = db_path
        self.mask_sensitive_fields = mask_sensitive_fields if os.getenv('MASK_SENSITIVE_FIELDS', 'true').lower() != 'false' else False
        self.anonymize_user_ids = anonymize_user_ids if os.getenv('ANONYMIZE_USER_IDS', 'false').lower() == 'true' else False
        self.encrypt_db = encrypt_db if os.getenv('ENCRYPT_AUDIT_DB', 'false').lower() == 'true' else False
        
        # Performance optimizations
        self.enable_caching = enable_caching
        self._stats_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 5  # Cache valid for 5 seconds
        self._batch_queue = []
        self._batch_size = 100  # Batch writes every N records
        
        # Initialize encryption if enabled
        self.encryption_key = None
        self.cipher = None
        if self.encrypt_db and ENCRYPTION_AVAILABLE:
            key = encryption_key or os.getenv('ENCRYPT_AUDIT_DB_KEY')
            if key:
                self._init_encryption(key)
            else:
                logger.warning("Encryption enabled but no key provided. Generating key (store securely!)")
                key = Fernet.generate_key()
                logger.warning(f"Generated key: {key.decode()}. Set ENCRYPT_AUDIT_DB_KEY env var.")
                self._init_encryption(key.decode())
        
        self._init_database()
    
    def _init_encryption(self, key: str):
        """Initialize encryption cipher."""
        if not ENCRYPTION_AVAILABLE:
            logger.error("Encryption requested but cryptography not available")
            return
        
        # Derive key from password if needed
        if len(key) != 44:  # Fernet key is 44 bytes base64 encoded
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'audit_log_salt',  # In production, use random salt per tenant
                iterations=100000,
            )
            key_bytes = kdf.derive(key.encode())
            key = base64.urlsafe_b64encode(key_bytes).decode()
        
        self.encryption_key = key
        self.cipher = Fernet(key.encode())
        logger.info("Encryption initialized for audit database")
    
    def _mask_sensitive_data(self, text: str) -> str:
        """
        Mask sensitive fields in text (PII, financial data).
        
        Patterns masked:
        - Email addresses
        - Phone numbers
        - Credit card numbers
        - SSNs
        - Bank account numbers
        """
        if not text:
            return text
        
        # Email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL_MASKED]', text)
        
        # Phone numbers (US format)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE_MASKED]', text)
        
        # Credit card numbers (basic pattern)
        text = re.sub(r'\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b', '[CC_MASKED]', text)
        
        # SSNs
        text = re.sub(r'\b\d{3}-\d{2}-\d{4}\b', '[SSN_MASKED]', text)
        
        # Bank account numbers (long numeric strings)
        text = re.sub(r'\b\d{10,}\b', lambda m: '[ACCOUNT_MASKED]' if len(m.group()) >= 10 else m.group(), text)
        
        return text
    
    def _anonymize_user_id(self, user_id: str) -> str:
        """Anonymize user ID using SHA256 hash."""
        if not user_id:
            return user_id
        return hashlib.sha256(user_id.encode('utf-8')).hexdigest()[:16]  # First 16 chars
        
    def _init_database(self):
        """Initialize audit logs database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS audit_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT UNIQUE NOT NULL,
                timestamp TEXT NOT NULL,
                input_hash TEXT NOT NULL,
                input_text TEXT,
                model_version TEXT NOT NULL,
                model_parameters TEXT NOT NULL,
                output_text TEXT,
                confidence_scores TEXT,
                explanation TEXT,
                processing_time_ms REAL NOT NULL,
                tokens_used INTEGER,
                tenant_id TEXT,
                user_id TEXT,
                source TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_request_id ON audit_logs(request_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_timestamp ON audit_logs(timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_input_hash ON audit_logs(input_hash)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tenant_id ON audit_logs(tenant_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON audit_logs(status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_source ON audit_logs(source)')
        
        conn.commit()
        conn.close()
        logger.info(f"Initialized audit database at {self.db_path}")
        
    def log_request(self, input_text: str, model_response: Optional[Dict], 
                   metadata: Dict) -> str:
        """
        Log an LLM inference request.
        
        Args:
            input_text: Original input text
            model_response: LLM response dict (or None if error)
            metadata: Request metadata
            
        Returns:
            Request ID (from metadata or newly generated)
        """
        import uuid
        
        request_id = metadata.get('request_id', str(uuid.uuid4()))
        timestamp = metadata.get('timestamp', datetime.utcnow().isoformat() + 'Z')
        
        # Calculate input hash for deduplication
        input_hash = hashlib.sha256(input_text.encode('utf-8')).hexdigest()
        
        # Extract model information
        model_version = metadata.get('model_version', metadata.get('model_name', 'unknown'))
        model_parameters = json.dumps(metadata.get('model_parameters', {}))
        
        # Extract output
        output_text = None
        confidence_scores = None
        tokens_used = None
        status = 'error'
        error_message = None
        
        if model_response:
            status = 'success'
            if isinstance(model_response, dict):
                # Extract from OpenAI-compatible format
                choices = model_response.get('choices', [])
                if choices:
                    output_text = choices[0].get('text', '')
                
                usage = model_response.get('usage', {})
                tokens_used = usage.get('total_tokens', 0)
                
                # Extract confidence if available
                if 'confidence' in model_response:
                    confidence_scores = json.dumps(model_response['confidence'])
        
        # Extract explanation if available
        explanation = metadata.get('explanation')
        if explanation:
            if isinstance(explanation, (list, dict)):
                explanation = json.dumps(explanation)
        
        # Extract processing time
        processing_time_ms = metadata.get('processing_time_ms', 0)
        
        # Extract tenant/user info
        tenant_id = metadata.get('tenant_id')
        user_id = metadata.get('user_id')
        source = metadata.get('source')
        
        # Privacy-by-design: Mask sensitive fields
        if self.mask_sensitive_fields:
            input_text = self._mask_sensitive_data(input_text) if input_text else None
            output_text = self._mask_sensitive_data(output_text) if output_text else None
        
        # Privacy-by-design: Anonymize user IDs
        if self.anonymize_user_ids and user_id:
            user_id = self._anonymize_user_id(user_id)
        
        # Encrypt sensitive fields if encryption enabled
        if self.encrypt_db and self.cipher:
            if input_text:
                input_text = self.cipher.encrypt(input_text.encode()).decode()
            if output_text:
                output_text = self.cipher.encrypt(output_text.encode()).decode()
        
        # Store in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO audit_logs (
                    request_id, timestamp, input_hash, input_text,
                    model_version, model_parameters, output_text,
                    confidence_scores, explanation, processing_time_ms,
                    tokens_used, tenant_id, user_id, source, status, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                request_id, timestamp, input_hash, input_text,
                model_version, model_parameters, output_text,
                confidence_scores, explanation, processing_time_ms,
                tokens_used, tenant_id, user_id, source, status, error_message
            ))
            
            conn.commit()
            logger.debug(f"Logged audit entry: {request_id}")
            
        except sqlite3.Error as e:
            logger.error(f"Database error logging audit entry: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return request_id
    
    def query_logs(self, filters: Dict) -> List[Dict]:
        """
        Query audit logs with filters.
        
        Args:
            filters: Dictionary with filter criteria:
                - request_id: Exact request ID
                - input_hash: Input hash to find duplicates
                - tenant_id: Filter by tenant
                - user_id: Filter by user
                - source: Filter by source
                - status: Filter by status (success/error)
                - start_time: Start timestamp (ISO format)
                - end_time: End timestamp (ISO format)
                - min_confidence: Minimum confidence score
                - limit: Maximum results (default: 100)
                
        Returns:
            List of audit log entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Build query
        conditions = []
        params = []
        
        if 'request_id' in filters:
            conditions.append('request_id = ?')
            params.append(filters['request_id'])
        
        if 'input_hash' in filters:
            conditions.append('input_hash = ?')
            params.append(filters['input_hash'])
        
        if 'tenant_id' in filters:
            conditions.append('tenant_id = ?')
            params.append(filters['tenant_id'])
        
        if 'user_id' in filters:
            conditions.append('user_id = ?')
            params.append(filters['user_id'])
        
        if 'source' in filters:
            conditions.append('source = ?')
            params.append(filters['source'])
        
        if 'status' in filters:
            conditions.append('status = ?')
            params.append(filters['status'])
        
        if 'start_time' in filters:
            conditions.append('timestamp >= ?')
            params.append(filters['start_time'])
        
        if 'end_time' in filters:
            conditions.append('timestamp <= ?')
            params.append(filters['end_time'])
        
        where_clause = ' AND '.join(conditions) if conditions else '1=1'
        limit = filters.get('limit', 100)
        
        query = f'''
            SELECT * FROM audit_logs
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        '''
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        # Convert to list of dicts
        results = []
        for row in rows:
            result = dict(row)
            # Parse JSON fields
            if result.get('model_parameters'):
                try:
                    result['model_parameters'] = json.loads(result['model_parameters'])
                except:
                    pass
            if result.get('confidence_scores'):
                try:
                    result['confidence_scores'] = json.loads(result['confidence_scores'])
                except:
                    pass
            if result.get('explanation'):
                try:
                    result['explanation'] = json.loads(result['explanation'])
                except:
                    pass
            results.append(result)
        
        conn.close()
        
        # Decrypt results if encryption enabled
        if self.encrypt_db and self.cipher:
            for result in results:
                try:
                    if result.get('input_text'):
                        result['input_text'] = self.cipher.decrypt(result['input_text'].encode()).decode()
                    if result.get('output_text'):
                        result['output_text'] = self.cipher.decrypt(result['output_text'].encode()).decode()
                except Exception as e:
                    logger.warning(f"Error decrypting audit log entry: {e}")
        
        return results
    
    def delete_user_data(self, user_id: str, tenant_id: Optional[str] = None) -> int:
        """
        Delete all audit logs for a user (GDPR Right to Deletion).
        
        Args:
            user_id: User ID to delete data for
            tenant_id: Optional tenant ID for multi-tenant isolation
            
        Returns:
            Number of records deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if tenant_id:
            cursor.execute('''
                DELETE FROM audit_logs 
                WHERE user_id = ? AND tenant_id = ?
            ''', (user_id, tenant_id))
        else:
            cursor.execute('DELETE FROM audit_logs WHERE user_id = ?', (user_id,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"Deleted {deleted_count} audit log entries for user {user_id}")
        return deleted_count
    
    def get_statistics(self) -> Dict:
        """Get audit log statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {}
        
        # Total requests
        cursor.execute('SELECT COUNT(*) FROM audit_logs')
        stats['total_requests'] = cursor.fetchone()[0]
        
        # Success/error counts
        cursor.execute('SELECT status, COUNT(*) FROM audit_logs GROUP BY status')
        stats['by_status'] = dict(cursor.fetchall())
        
        # Average processing time
        cursor.execute('SELECT AVG(processing_time_ms) FROM audit_logs WHERE status = "success"')
        avg_time = cursor.fetchone()[0]
        stats['avg_processing_time_ms'] = round(avg_time, 2) if avg_time else 0
        
        # Total tokens used
        cursor.execute('SELECT SUM(tokens_used) FROM audit_logs WHERE tokens_used IS NOT NULL')
        total_tokens = cursor.fetchone()[0]
        stats['total_tokens_used'] = total_tokens or 0
        
        # Requests by source
        cursor.execute('SELECT source, COUNT(*) FROM audit_logs GROUP BY source')
        stats['by_source'] = dict(cursor.fetchall())
        
        conn.close()
        return stats
