"""
Test producer for sending financial documents to Kafka.

This script sends sample financial documents to the Kafka topic
for processing by the LLM processor.
"""

import json
import logging
import sys
import time
import uuid
from datetime import datetime
from typing import List, Optional

from kafka import KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DocumentProducer:
    """Produces financial documents to Kafka."""
    
    def __init__(self, brokers: List[str], topic: str):
        self.brokers = brokers
        self.topic = topic
        
        self.producer = KafkaProducer(
            bootstrap_servers=brokers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1,
            compression_type='gzip',
            linger_ms=10,
            batch_size=16384
        )
        
    def send_document(self, text: str, source: str = 'test', 
                     request_id: Optional[str] = None) -> bool:
        """
        Send a document to Kafka.
        
        Args:
            text: Document text content
            source: Source identifier
            request_id: Optional request ID (generated if not provided)
            
        Returns:
            True if successful, False otherwise
        """
        if not request_id:
            request_id = str(uuid.uuid4())
            
        message = {
            'request_id': request_id,
            'text': text,
            'source': source,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'metadata': {
                'producer': 'test_producer',
                'version': '1.0.0'
            }
        }
        
        try:
            future = self.producer.send(
                self.topic,
                key=request_id,
                value=message
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Sent document: topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, "
                f"offset={record_metadata.offset}, "
                f"request_id={request_id}"
            )
            
            return True
            
        except KafkaError as e:
            logger.error(f"Failed to send document: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending document: {e}", exc_info=True)
            return False
            
    def flush(self, timeout: float = 10.0):
        """Flush all pending messages."""
        self.producer.flush(timeout=timeout)
        
    def close(self):
        """Close the producer."""
        self.flush()
        self.producer.close()


def get_sample_documents() -> List[dict]:
    """Get sample financial documents for testing."""
    return [
        {
            'text': 'Apple Inc. reported Q4 2024 revenue of $89.5 billion, up 1% year-over-year. '
                   'iPhone revenue was $43.8 billion, Services revenue reached $22.3 billion. '
                   'The company announced a $110 billion share buyback program.',
            'source': 'earnings-report'
        },
        {
            'text': 'Microsoft Corporation announced Q4 2024 revenue of $61.9 billion, '
                   'increasing 13% YoY. Azure cloud revenue grew 28%, Office 365 revenue '
                   'increased 15%. The company raised its dividend by 10%.',
            'source': 'earnings-report'
        },
        {
            'text': 'SEC filing 10-K: Amazon.com Inc. reported annual revenue of $574.8 billion '
                   'for fiscal year 2024. AWS segment revenue was $90.8 billion, representing '
                   '16% of total revenue. Operating income was $30.4 billion.',
            'source': 'sec-filing'
        },
        {
            'text': 'Breaking: Tesla Motors announced delivery of 484,507 vehicles in Q4 2024, '
                   'exceeding analyst expectations. Model Y deliveries reached 461,538 units. '
                   'The company expects to produce 2 million vehicles in 2025.',
            'source': 'news-article'
        },
        {
            'text': 'Federal Reserve maintains federal funds rate at 5.25-5.50% following FOMC meeting. '
                   'The committee noted continued strength in labor markets and elevated inflation. '
                   'Projections indicate potential rate cuts in 2025 if inflation trends downward.',
            'source': 'fed-announcement'
        },
        {
            'text': 'JPMorgan Chase reported Q4 2024 net income of $9.3 billion, down 15% YoY. '
                   'Net interest income was $22.9 billion. The bank set aside $2.4 billion for '
                   'credit losses. Return on equity was 15%.',
            'source': 'earnings-report'
        }
    ]


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Send test documents to Kafka')
    parser.add_argument(
        '--brokers',
        default='localhost:9092',
        help='Kafka broker addresses (comma-separated)'
    )
    parser.add_argument(
        '--topic',
        default='financial-documents',
        help='Kafka topic name'
    )
    parser.add_argument(
        '--count',
        type=int,
        default=1,
        help='Number of documents to send (default: 1, use 0 for all samples)'
    )
    parser.add_argument(
        '--delay',
        type=float,
        default=1.0,
        help='Delay between messages in seconds'
    )
    
    args = parser.parse_args()
    
    brokers = args.brokers.split(',')
    producer = DocumentProducer(brokers, args.topic)
    
    sample_docs = get_sample_documents()
    
    try:
        if args.count == 0:
            # Send all samples
            docs_to_send = sample_docs
        else:
            # Send specified count
            docs_to_send = sample_docs[:args.count]
            
        logger.info(f"Sending {len(docs_to_send)} document(s) to topic '{args.topic}'...")
        
        success_count = 0
        for i, doc in enumerate(docs_to_send, 1):
            logger.info(f"Sending document {i}/{len(docs_to_send)}: {doc['source']}")
            
            if producer.send_document(
                text=doc['text'],
                source=doc['source']
            ):
                success_count += 1
                
            if i < len(docs_to_send):
                time.sleep(args.delay)
                
        logger.info(f"Successfully sent {success_count}/{len(docs_to_send)} documents")
        
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
    finally:
        producer.close()


if __name__ == '__main__':
    main()

