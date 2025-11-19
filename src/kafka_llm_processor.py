"""
Kafka consumer that processes financial documents through LLM inference.

This service consumes documents from Kafka, processes them via vLLM,
and publishes results to an output topic.
"""

import json
import logging
import os
import signal
import sys
import time
from datetime import datetime
from typing import Dict, Optional

import requests
from kafka import KafkaConsumer, KafkaProducer
from kafka.errors import KafkaError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('kafka_llm_processor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class LLMProcessor:
    """Handles LLM inference requests."""
    
    def __init__(self, llm_url: str, model_name: str, timeout: int = 30):
        self.llm_url = llm_url
        self.model_name = model_name
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        
    def process_document(self, document_text: str, max_tokens: int = 200) -> Optional[Dict]:
        """
        Process a document through LLM inference.
        Supports both OpenAI-compatible API and Ollama API.
        
        Args:
            document_text: The text content to process
            max_tokens: Maximum tokens in response
            
        Returns:
            LLM response dict or None if error
        """
        prompt = f"Extract key information from the following financial document:\n\n{document_text}"
        
        # Use Ollama API (default) or OpenAI-compatible API
        # Check if URL contains ollama port (11434) or use OpenAI-compatible
        use_ollama = '11434' in self.llm_url or 'ollama' in self.llm_url.lower()
        
        if not use_ollama:
            # Try OpenAI-compatible API first (vLLM, OpenAI, etc.)
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "max_tokens": max_tokens,
                "temperature": 0.7,
                "top_p": 0.9
            }
            
            try:
                response = self.session.post(
                    f"{self.llm_url}/v1/completions",
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                return result
            except (requests.exceptions.RequestException, ValueError, json.JSONDecodeError) as e:
                logger.warning(f"OpenAI-compatible API failed, trying Ollama: {e}")
                use_ollama = True
        
        if use_ollama:
            # Use Ollama API format
            try:
                ollama_payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,  # Disable streaming to get single JSON response
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "num_predict": max_tokens
                    }
                }
                
                response = self.session.post(
                    f"{self.llm_url}/api/generate",
                    json=ollama_payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Parse JSON response
                # Ollama returns single JSON object when stream=False
                try:
                    result = response.json()
                except json.JSONDecodeError as e:
                    # Handle case where response might have extra data
                    response_text = response.text.strip()
                    # Try to parse just the JSON part
                    if '\n' in response_text:
                        # Multiple lines - take the last complete JSON
                        lines = [l.strip() for l in response_text.split('\n') if l.strip()]
                        result = None
                        for line in reversed(lines):
                            try:
                                result = json.loads(line)
                                if isinstance(result, dict) and 'response' in result:
                                    break
                            except json.JSONDecodeError:
                                continue
                        if result is None:
                            raise json.JSONDecodeError("No valid JSON found", response_text, 0)
                    else:
                        # Single line - try to extract JSON
                        # Remove any trailing non-JSON text
                        try:
                            result = json.loads(response_text)
                        except json.JSONDecodeError:
                            # Try to find JSON object boundaries
                            start = response_text.find('{')
                            end = response_text.rfind('}') + 1
                            if start >= 0 and end > start:
                                result = json.loads(response_text[start:end])
                            else:
                                raise
                
                # Convert Ollama format to OpenAI-compatible
                return {
                    "choices": [{
                        "text": result.get('response', ''),
                        "index": 0,
                        "finish_reason": "stop" if result.get('done') else "length"
                    }],
                    "usage": {
                        "prompt_tokens": result.get('prompt_eval_count', len(prompt.split())),
                        "completion_tokens": result.get('eval_count', len(result.get('response', '').split())),
                        "total_tokens": result.get('prompt_eval_count', 0) + result.get('eval_count', 0)
                    }
                }
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                if 'response' in locals():
                    logger.error(f"Response text (first 500 chars): {response.text[:500]}")
                return None
            except requests.exceptions.Timeout:
                logger.error(f"LLM request timeout after {self.timeout}s")
                return None
            except requests.exceptions.RequestException as e:
                logger.error(f"LLM request failed: {e}")
                return None
            except Exception as e:
                logger.error(f"Unexpected error in LLM processing: {e}", exc_info=True)
                return None


class KafkaLLMProcessor:
    """Main processor that consumes from Kafka and processes via LLM."""
    
    def __init__(self, config: Dict):
        self.config = config
        self.running = True
        self.processed_count = 0
        self.error_count = 0
        
        # Initialize LLM processor
        self.llm_processor = LLMProcessor(
            llm_url=config['llm_url'],
            model_name=config['model_name'],
            timeout=config.get('llm_timeout', 30)
        )
        
        # Initialize Kafka consumer
        self.consumer = KafkaConsumer(
            config['input_topic'],
            bootstrap_servers=config['kafka_brokers'],
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            group_id=config.get('consumer_group', 'llm-processor-group'),
            auto_offset_reset='earliest',
            enable_auto_commit=True,
            auto_commit_interval_ms=5000,
            max_poll_records=10,
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000
        )
        
        # Initialize Kafka producer
        self.producer = KafkaProducer(
            bootstrap_servers=config['kafka_brokers'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1,
            compression_type='gzip',
            linger_ms=10,
            batch_size=16384
        )
        
        # Register signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
        
    def _create_result_message(self, original_message: Dict, llm_response: Dict, 
                              processing_time_ms: float) -> Dict:
        """Create structured result message."""
        return {
            'request_id': original_message.get('request_id', f"req_{int(time.time() * 1000)}"),
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'source': original_message.get('source', 'unknown'),
            'original_text': original_message.get('text', ''),
            'llm_response': llm_response.get('choices', [{}])[0].get('text', '') if llm_response else None,
            'model_used': self.config['model_name'],
            'processing_time_ms': round(processing_time_ms, 2),
            'tokens_used': llm_response.get('usage', {}).get('total_tokens', 0) if llm_response else 0,
            'status': 'success' if llm_response else 'error'
        }
        
    def process_message(self, message) -> bool:
        """
        Process a single Kafka message.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            document = message.value
            message_key = message.key
            
            if not document or 'text' not in document:
                logger.warning(f"Invalid message format: {document}")
                self.error_count += 1
                return False
                
            document_text = document['text']
            logger.info(f"Processing document from source: {document.get('source', 'unknown')}")
            
            # Process through LLM
            start_time = time.time()
            llm_response = self.llm_processor.process_document(document_text)
            processing_time = (time.time() - start_time) * 1000
            
            # Create result message
            result_message = self._create_result_message(
                document,
                llm_response,
                processing_time
            )
            
            # Send to output topic
            future = self.producer.send(
                self.config['output_topic'],
                key=message_key,
                value=result_message
            )
            
            # Wait for send confirmation
            record_metadata = future.get(timeout=10)
            logger.info(
                f"Processed message: topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, offset={record_metadata.offset}, "
                f"time={processing_time:.2f}ms"
            )
            
            self.processed_count += 1
            return True
            
        except KafkaError as e:
            logger.error(f"Kafka error processing message: {e}")
            self.error_count += 1
            return False
        except Exception as e:
            logger.error(f"Unexpected error processing message: {e}", exc_info=True)
            self.error_count += 1
            return False
            
    def run(self):
        """Main processing loop."""
        logger.info("Starting Kafka LLM processor...")
        logger.info(f"Consuming from topic: {self.config['input_topic']}")
        logger.info(f"Publishing to topic: {self.config['output_topic']}")
        logger.info(f"LLM endpoint: {self.config['llm_url']}")
        
        try:
            while self.running:
                message_batch = self.consumer.poll(timeout_ms=1000, max_records=10)
                
                if not message_batch:
                    continue
                    
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        if not self.running:
                            break
                        self.process_message(message)
                        
                # Log stats periodically
                if self.processed_count % 100 == 0:
                    logger.info(
                        f"Stats: processed={self.processed_count}, "
                        f"errors={self.error_count}, "
                        f"success_rate={100 * (1 - self.error_count / max(self.processed_count, 1)):.1f}%"
                    )
                    
        except Exception as e:
            logger.error(f"Fatal error in processing loop: {e}", exc_info=True)
        finally:
            self.shutdown()
            
    def shutdown(self):
        """Gracefully shutdown the processor."""
        logger.info("Shutting down processor...")
        logger.info(f"Final stats: processed={self.processed_count}, errors={self.error_count}")
        
        try:
            self.consumer.close()
            self.producer.flush(timeout=10)
            self.producer.close()
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


def load_config() -> Dict:
    """Load configuration from environment variables with defaults."""
    return {
        'kafka_brokers': os.getenv('KAFKA_BROKERS', 'localhost:9092').split(','),
        'input_topic': os.getenv('INPUT_TOPIC', 'financial-documents'),
        'output_topic': os.getenv('OUTPUT_TOPIC', 'llm-results'),
        'consumer_group': os.getenv('CONSUMER_GROUP', 'llm-processor-group'),
        'llm_url': os.getenv('LLM_URL', 'http://localhost:11434'),  # Ollama default port
        'model_name': os.getenv('MODEL_NAME', 'llama2'),  # Default Ollama model
        'llm_timeout': int(os.getenv('LLM_TIMEOUT', '60'))  # Longer timeout for Ollama
    }


def main():
    """Main entry point."""
    config = load_config()
    processor = KafkaLLMProcessor(config)
    
    try:
        processor.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

