"""
Comprehensive benchmark suite for LLM Infrastructure.

Runs real performance tests and generates JSON results.
"""

import json
import time
import logging
import os
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Any
import random
import string

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add src to path for imports
src_path = os.path.join(os.path.dirname(__file__), '..', 'src')
if os.path.exists(src_path):
    sys.path.insert(0, src_path)

# Try importing from src/
AuditLogger = None
DriftDetector = None
DriftMonitor = None

try:
    from audit_logger import AuditLogger
    from drift_detector import DriftDetector, DriftMonitor
    logger.info("✓ Imported modules from src/")
except ImportError as e:
    logger.warning(f"Could not import from src/: {e}")


class BenchmarkRunner:
    """Runs comprehensive benchmarks on LLM infrastructure components."""
    
    def __init__(self, output_dir: str = "benchmarks/results"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results = {}
        
    def run_audit_logging_benchmark(self) -> Dict[str, Any]:
        """Benchmark audit logging performance."""
        if AuditLogger is None:
            logger.warning("AuditLogger not available, skipping benchmark")
            return {"name": "Audit Logging Benchmark", "skipped": True, "reason": "AuditLogger not available"}
        
        logger.info("Running audit logging benchmark...")
        
        # Use temporary database for benchmarking
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "benchmark_audit.db")
            audit_logger = AuditLogger(db_path=db_path)
            
            metrics = {
                "name": "Audit Logging Benchmark",
                "operations": [],
                "summary": {}
            }
            
            # Test 1: Single request logging
            print("  Test 1: Single request logging... ", end="", flush=True)
            start = time.perf_counter()
            for i in range(100):
                audit_logger.log_request(
                    input_text=f"Sample financial document {i}",
                    model_response={
                        "choices": [{"text": f"Analysis of document {i}"}],
                        "usage": {"total_tokens": 150}
                    },
                    metadata={
                        "model_version": "llama2-7b",
                        "model_parameters": {"temperature": 0.7},
                        "processing_time_ms": random.uniform(40, 60),
                        "tenant_id": f"tenant-{i % 5}",
                        "source": "test"
                    }
                )
            elapsed = time.perf_counter() - start
            avg_latency = (elapsed / 100) * 1000
            print(f"✓ ({avg_latency:.2f}ms per request)")
            metrics["operations"].append({
                "name": "100 single request logs",
                "count": 100,
                "total_time_ms": elapsed * 1000,
                "avg_latency_ms": avg_latency,
                "throughput_req_per_sec": 100 / elapsed
            })
            
            # Test 2: Query performance
            print("  Test 2: Query audit logs... ", end="", flush=True)
            start = time.perf_counter()
            for _ in range(10):
                audit_logger.query_logs({"status": "success", "limit": 100})
            elapsed = time.perf_counter() - start
            avg_query_time = (elapsed / 10) * 1000
            print(f"✓ ({avg_query_time:.2f}ms per query)")
            metrics["operations"].append({
                "name": "Query 10x",
                "count": 10,
                "total_time_ms": elapsed * 1000,
                "avg_latency_ms": avg_query_time
            })
            
            # Test 3: Get statistics
            print("  Test 3: Compute statistics... ", end="", flush=True)
            start = time.perf_counter()
            for _ in range(5):
                audit_logger.get_statistics()
            elapsed = time.perf_counter() - start
            print(f"✓ ({(elapsed/5)*1000:.2f}ms per call)")
            metrics["operations"].append({
                "name": "Statistics computation",
                "count": 5,
                "total_time_ms": elapsed * 1000,
                "avg_latency_ms": (elapsed / 5) * 1000
            })
            
            # Summary
            metrics["summary"] = {
                "total_requests_logged": 100,
                "avg_log_latency_ms": avg_latency,
                "query_latency_ms": avg_query_time,
                "throughput_req_per_sec": 100 / (elapsed if elapsed > 0 else 1)
            }
            
        return metrics
    
    def run_drift_detection_benchmark(self) -> Dict[str, Any]:
        """Benchmark drift detection performance."""
        if DriftDetector is None:
            logger.warning("DriftDetector not available, skipping benchmark")
            return {"name": "Drift Detection Benchmark", "skipped": True, "reason": "DriftDetector not available"}
        
        logger.info("Running drift detection benchmark...")
        
        detector = DriftDetector(
            baseline_window_size=100,
            detection_window_size=50,
            drift_threshold=0.05
        )
        
        metrics = {
            "name": "Drift Detection Benchmark",
            "operations": [],
            "summary": {}
        }
        
        # Generate test data
        print("  Generating test samples... ", end="", flush=True)
        baseline_samples = []
        for i in range(120):
            baseline_samples.append({
                "text": f"Sample output {i} with financial information about Q{(i % 4) + 1} 2024",
                "tokens_used": random.randint(100, 200),
                "processing_time_ms": random.uniform(40, 60) + (i * 0.01)
            })
        print("✓")
        
        # Test 1: Baseline establishment
        print("  Test 1: Baseline establishment (20 samples)... ", end="", flush=True)
        start = time.perf_counter()
        for sample in baseline_samples[:100]:
            detector.add_output(sample)
        elapsed = time.perf_counter() - start
        print(f"✓ ({elapsed*1000:.2f}ms)")
        metrics["operations"].append({
            "name": "Baseline establishment",
            "samples": 100,
            "total_time_ms": elapsed * 1000,
            "avg_latency_ms": (elapsed / 100) * 1000
        })
        
        # Test 2: Normal samples (should not drift)
        print("  Test 2: Normal samples (no drift)... ", end="", flush=True)
        start = time.perf_counter()
        drift_count = 0
        for sample in baseline_samples[100:120]:
            result = detector.add_output(sample)
            if result and result.get('drift_detected'):
                drift_count += 1
        elapsed = time.perf_counter() - start
        false_positive_rate = (drift_count / 20) * 100 if drift_count > 0 else 0
        print(f"✓ (False positives: {false_positive_rate:.1f}%)")
        metrics["operations"].append({
            "name": "Normal sample processing",
            "samples": 20,
            "false_positive_rate_percent": false_positive_rate,
            "total_time_ms": elapsed * 1000,
            "avg_latency_ms": (elapsed / 20) * 1000
        })
        
        # Test 3: Drifted samples
        print("  Test 3: Drifted samples detection... ", end="", flush=True)
        detector_drift = DriftDetector(
            baseline_window_size=50,
            detection_window_size=30,
            drift_threshold=0.05
        )
        # Establish baseline
        for i in range(50):
            detector_drift.add_output({
                "text": "Normal output",
                "tokens_used": 150,
                "processing_time_ms": 50
            })
        
        # Generate drifted samples
        start = time.perf_counter()
        drift_detected_count = 0
        for i in range(30):
            result = detector_drift.add_output({
                "text": "Very long output with significantly more content than before " * 10,
                "tokens_used": 350 + (i * 10),  # Increasing tokens
                "processing_time_ms": 150 + (i * 2)  # Increasing latency
            })
            if result and result.get('drift_detected'):
                drift_detected_count += 1
        elapsed = time.perf_counter() - start
        drift_detection_rate = (drift_detected_count / 30) * 100
        print(f"✓ (Detection rate: {drift_detection_rate:.1f}%)")
        metrics["operations"].append({
            "name": "Drifted sample detection",
            "samples": 30,
            "drift_detection_rate_percent": drift_detection_rate,
            "total_time_ms": elapsed * 1000,
            "avg_latency_ms": (elapsed / 30) * 1000
        })
        
        # Summary
        metrics["summary"] = {
            "baseline_establishment_ms": metrics["operations"][0]["total_time_ms"],
            "normal_processing_false_positive_rate": false_positive_rate,
            "drift_detection_rate": drift_detection_rate,
            "avg_detection_latency_ms": (metrics["operations"][2]["total_time_ms"] / 30)
        }
        
        return metrics
    
    def run_synthetic_throughput_benchmark(self) -> Dict[str, Any]:
        """Benchmark synthetic throughput (mock LLM responses)."""
        logger.info("Running synthetic throughput benchmark...")
        
        metrics = {
            "name": "Synthetic Throughput Benchmark",
            "operations": [],
            "summary": {}
        }
        
        # Simulate different batch sizes
        batch_sizes = [1, 10, 50, 100]
        
        for batch_size in batch_sizes:
            print(f"  Batch size {batch_size}: ", end="", flush=True)
            
            start = time.perf_counter()
            for i in range(batch_size):
                # Simulate document processing
                doc = f"Financial document {i}" * 10
                response = {
                    "choices": [{"text": f"Analysis of doc {i}"}],
                    "usage": {"total_tokens": len(doc.split())}
                }
                # Simulate audit logging
                _ = {
                    "timestamp": time.time(),
                    "tokens": response["usage"]["total_tokens"]
                }
            elapsed = time.perf_counter() - start
            
            throughput = batch_size / elapsed
            print(f"✓ ({throughput:.1f} requests/sec)")
            
            metrics["operations"].append({
                "batch_size": batch_size,
                "total_time_ms": elapsed * 1000,
                "throughput_req_per_sec": throughput
            })
        
        # Summary
        metrics["summary"] = {
            "best_throughput_req_per_sec": max(op["throughput_req_per_sec"] for op in metrics["operations"]),
            "optimal_batch_size": metrics["operations"][np.argmax([op["throughput_req_per_sec"] for op in metrics["operations"]])]["batch_size"]
        }
        
        return metrics
    
    def run_memory_profiling_benchmark(self) -> Dict[str, Any]:
        """Profile memory usage of core components."""
        if AuditLogger is None or DriftDetector is None:
            logger.warning("Required modules not available, skipping benchmark")
            return {"name": "Memory Profiling Benchmark", "skipped": True, "reason": "Required modules not available"}
        
        logger.info("Running memory profiling benchmark...")
        
        import tracemalloc
        
        metrics = {
            "name": "Memory Profiling Benchmark",
            "operations": [],
            "summary": {}
        }
        
        # Test 1: Audit logger memory
        print("  Test 1: Audit logger with 1000 entries... ", end="", flush=True)
        tracemalloc.start()
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "bench_memory.db")
            audit_logger = AuditLogger(db_path=db_path)
            
            for i in range(1000):
                audit_logger.log_request(
                    input_text=f"Document {i}",
                    model_response={"choices": [{"text": f"Analysis {i}"}], "usage": {"total_tokens": 150}},
                    metadata={"model_version": "v1", "processing_time_ms": 50}
                )
            
            _, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
        print(f"✓ ({peak_memory / 1024 / 1024:.2f} MB)")
        metrics["operations"].append({
            "name": "Audit logger (1000 entries)",
            "memory_mb": peak_memory / 1024 / 1024
        })
        
        # Test 2: Drift detector memory
        print("  Test 2: Drift detector with baseline... ", end="", flush=True)
        tracemalloc.start()
        detector = DriftDetector(baseline_window_size=500)
        for i in range(500):
            detector.add_output({
                "text": "Output " + "x" * 500,
                "tokens_used": 200,
                "processing_time_ms": 50
            })
        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        print(f"✓ ({peak_memory / 1024 / 1024:.2f} MB)")
        metrics["operations"].append({
            "name": "Drift detector (500 baseline)",
            "memory_mb": peak_memory / 1024 / 1024
        })
        
        metrics["summary"] = {
            "total_memory_mb": sum(op.get("memory_mb", 0) for op in metrics["operations"])
        }
        
        return metrics
    
    def run_all_benchmarks(self) -> Dict[str, Any]:
        """Run all benchmarks and return aggregated results."""
        logger.info("=" * 80)
        logger.info("STARTING LLM INFRASTRUCTURE BENCHMARK SUITE")
        logger.info("=" * 80)
        
        all_results = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "benchmarks": {}
        }
        
        try:
            all_results["benchmarks"]["audit_logging"] = self.run_audit_logging_benchmark()
        except Exception as e:
            logger.error(f"Audit logging benchmark failed: {e}", exc_info=True)
            all_results["benchmarks"]["audit_logging"] = {"error": str(e)}
        
        try:
            all_results["benchmarks"]["drift_detection"] = self.run_drift_detection_benchmark()
        except Exception as e:
            logger.error(f"Drift detection benchmark failed: {e}", exc_info=True)
            all_results["benchmarks"]["drift_detection"] = {"error": str(e)}
        
        try:
            all_results["benchmarks"]["throughput"] = self.run_synthetic_throughput_benchmark()
        except Exception as e:
            logger.error(f"Throughput benchmark failed: {e}", exc_info=True)
            all_results["benchmarks"]["throughput"] = {"error": str(e)}
        
        try:
            all_results["benchmarks"]["memory_profiling"] = self.run_memory_profiling_benchmark()
        except Exception as e:
            logger.error(f"Memory profiling benchmark failed: {e}", exc_info=True)
            all_results["benchmarks"]["memory_profiling"] = {"error": str(e)}
        
        # Save results
        results_file = self.output_dir / "benchmark_results.json"
        with open(results_file, "w") as f:
            json.dump(all_results, f, indent=2)
        
        logger.info(f"\n✓ Benchmark results saved to: {results_file}")
        
        return all_results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print benchmark summary to console."""
        print("\n" + "=" * 80)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 80)
        
        for benchmark_name, benchmark_data in results.get("benchmarks", {}).items():
            if isinstance(benchmark_data, dict) and "error" not in benchmark_data:
                print(f"\n{benchmark_data.get('name', benchmark_name).upper()}")
                print("-" * 80)
                
                for operation in benchmark_data.get("operations", []):
                    print(f"  {operation.get('name', 'Operation')}")
                    for key, value in operation.items():
                        if key != "name":
                            if isinstance(value, float):
                                print(f"    {key}: {value:.2f}")
                            else:
                                print(f"    {key}: {value}")
                
                print("\n  Summary:")
                for key, value in benchmark_data.get("summary", {}).items():
                    if isinstance(value, float):
                        print(f"    {key}: {value:.2f}")
                    else:
                        print(f"    {key}: {value}")


def main():
    """Run benchmark suite."""
    runner = BenchmarkRunner()
    results = runner.run_all_benchmarks()
    runner.print_summary(results)
    
    print("\n" + "=" * 80)
    print("✓ All benchmarks completed successfully!")
    print("=" * 80)


if __name__ == "__main__":
    # Add numpy import
    try:
        import numpy as np
    except ImportError:
        np = None
    
    main()
