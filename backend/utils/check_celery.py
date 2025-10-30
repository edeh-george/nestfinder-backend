import socket
from logging import getLogger

from celery import current_app

logger = getLogger("backend")


class CeleryHealthChecker:
    """Utility class to check Celery worker availability."""

    @staticmethod
    def is_celery_available() -> bool:
        """
        Check if Celery workers are available and responsive.

        Returns:
            bool: True if Celery is available and has active workers
        """
        try:
            inspect = current_app.control.inspect()
            active_workers = inspect.active()

            if active_workers:
                logger.debug(
                    f"Active Celery workers found: {list(active_workers.keys())}"
                )
                return True
            else:
                logger.warning("No active Celery workers found")
                return False

        except Exception as e:
            logger.warning(f"Error checking Celery availability: {str(e)}")
            return False

    @staticmethod
    def is_broker_reachable() -> bool:
        """
        Check if the Celery broker (Redis/RabbitMQ) is reachable.

        Returns:
            bool: True if broker is reachable
        """
        try:
            broker_url = current_app.conf.broker_url

            if not broker_url:
                return False

            # For Redis broker
            if broker_url.startswith("redis://"):
                from urllib.parse import urlparse

                import redis

                parsed = urlparse(broker_url)

                redis_client = redis.Redis(
                    host=parsed.hostname or "localhost",
                    port=parsed.port or 6379,
                    db=int(parsed.path.lstrip("/")) if parsed.path else 0,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                redis_client.ping()
                return True

            # For RabbitMQ broker
            elif broker_url.startswith("amqp://") or broker_url.startswith("pyamqp://"):
                # Simple socket check for RabbitMQ
                from urllib.parse import urlparse

                parsed = urlparse(broker_url)
                host = parsed.hostname or "localhost"
                port = parsed.port or 5672

                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((host, port))
                sock.close()
                return result == 0

            return False

        except Exception as e:
            logger.warning(f"Error checking broker reachability: {str(e)}")
            return False

    @classmethod
    def is_celery_ready(cls) -> bool:
        """
        Comprehensive check for Celery readiness.

        Returns:
            bool: True if Celery is ready to accept tasks
        """
        return cls.is_broker_reachable() and cls.is_celery_available()
