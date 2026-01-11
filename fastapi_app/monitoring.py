# fastapi_app/monitoring.py
import logging
import time
from typing import Dict, Any
from dataclasses import dataclass
from datetime import datetime
from prometheus_client import Counter, Histogram, Gauge

# Prometheus metrics
UPDATE_COUNTER = Counter('telegram_updates_total', 'Total Telegram updates', ['bot_id', 'type'])
PROCESSING_TIME = Histogram('update_processing_seconds', 'Update processing time', ['bot_id'])
QUEUE_SIZE = Gauge('redis_queue_size', 'Redis queue size', ['bot_id'])
ACTIVE_WORKERS = Gauge('active_workers_total', 'Active workers count', ['bot_id'])
ERROR_COUNTER = Counter('processing_errors_total', 'Processing errors', ['bot_id', 'error_type'])


@dataclass
class MetricsCollector:
    """Collect and report system metrics"""

    @staticmethod
    def record_update(bot_id: int, update_type: str):
        UPDATE_COUNTER.labels(bot_id=bot_id, type=update_type).inc()

    @staticmethod
    def record_processing_time(bot_id: int, duration: float):
        PROCESSING_TIME.labels(bot_id=bot_id).observe(duration)

    @staticmethod
    def update_queue_size(bot_id: int, size: int):
        QUEUE_SIZE.labels(bot_id=bot_id).set(size)

    @staticmethod
    def update_worker_count(bot_id: int, count: int):
        ACTIVE_WORKERS.labels(bot_id=bot_id).set(count)

    @staticmethod
    def record_error(bot_id: int, error_type: str):
        ERROR_COUNTER.labels(bot_id=bot_id, error_type=error_type).inc()


class PerformanceMonitor:
    """Monitor system performance"""

    def __init__(self):
        self.metrics = {}
        self.start_time = datetime.now()

    def track_performance(self, bot_id: int, operation: str, duration: float):
        """Track operation performance"""
        if bot_id not in self.metrics:
            self.metrics[bot_id] = {}

        if operation not in self.metrics[bot_id]:
            self.metrics[bot_id][operation] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0
            }

        stats = self.metrics[bot_id][operation]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['avg_time'] = stats['total_time'] / stats['count']

        # Log if operation takes too long
        if duration > 1.0:  # More than 1 second
            logging.warning(f"Slow operation: bot={bot_id}, operation={operation}, duration={duration:.2f}s")

    def get_report(self) -> Dict[str, Any]:
        """Get performance report"""
        report = {
            'uptime': (datetime.now() - self.start_time).total_seconds(),
            'bots': {}
        }

        for bot_id, operations in self.metrics.items():
            report['bots'][bot_id] = {
                'total_operations': sum(op['count'] for op in operations.values()),
                'operations': operations
            }

        return report