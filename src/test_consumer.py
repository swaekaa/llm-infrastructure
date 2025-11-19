"""
Test consumer for reading LLM results from Kafka.

This script consumes processed results from the output topic
to verify the end-to-end pipeline.
"""

import json
import logging
import sys
import signal
from datetime import datetime

from kafka import KafkaConsumer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ResultConsumer:
    """Consumes LLM processing results from Kafka."""
    
    def __init__(self, brokers: list, topic: str, group_id: str = 'test-consumer-group'):
        self.brokers = brokers
        self.topic = topic
        self.running = True
        
        self.consumer = KafkaConsumer(
            topic,
            bootstrap_servers=brokers,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            group_id=group_id,
            auto_offset_reset='latest',  # Only read new messages
            enable_auto_commit=True,
            consumer_timeout_ms=10000  # Timeout after 10s of no messages
        )
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
        
    def print_result(self, message):
        """Print formatted result message."""
        result = message.value
        
        print("\n" + "=" * 80)
        print(f"Request ID: {result.get('request_id', 'N/A')}")
        print(f"Source: {result.get('source', 'N/A')}")
        print(f"Timestamp: {result.get('timestamp', 'N/A')}")
        print(f"Status: {result.get('status', 'N/A')}")
        print(f"Processing Time: {result.get('processing_time_ms', 0):.2f}ms")
        print(f"Tokens Used: {result.get('tokens_used', 0)}")
        print("-" * 80)
        print("Original Text:")
        print(result.get('original_text', '')[:200] + "..." if len(result.get('original_text', '')) > 200 else result.get('original_text', ''))
        print("-" * 80)
        print("LLM Response:")
        print(result.get('llm_response', 'N/A'))
        print("=" * 80 + "\n")
        
    def consume(self, max_messages: int = None):
        """
        Consume messages from the topic.
        
        Args:
            max_messages: Maximum number of messages to consume (None for unlimited)
        """
        logger.info(f"Starting to consume from topic '{self.topic}'...")
        logger.info("Press Ctrl+C to stop\n")
        
        message_count = 0
        
        try:
            while self.running:
                message_batch = self.consumer.poll(timeout_ms=1000, max_records=10)
                
                if not message_batch:
                    continue
                    
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        if not self.running:
                            break
                            
                        self.print_result(message)
                        message_count += 1
                        
                        if max_messages and message_count >= max_messages:
                            logger.info(f"Reached maximum message count ({max_messages}), stopping...")
                            self.running = False
                            break
                            
        except KafkaError as e:
            logger.error(f"Kafka error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error: {e}", exc_info=True)
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Gracefully shutdown the consumer."""
        logger.info("Shutting down consumer...")
        try:
            self.consumer.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Consume LLM results from Kafka')
    parser.add_argument(
        '--brokers',
        default='localhost:9092',
        help='Kafka broker addresses (comma-separated)'
    )
    parser.add_argument(
        '--topic',
        default='llm-results',
        help='Kafka topic name'
    )
    parser.add_argument(
        '--max-messages',
        type=int,
        default=None,
        help='Maximum number of messages to consume (default: unlimited)'
    )
    
    args = parser.parse_args()
    
    brokers = args.brokers.split(',')
    consumer = ResultConsumer(brokers, args.topic)
    
    try:
        consumer.consume(max_messages=args.max_messages)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

