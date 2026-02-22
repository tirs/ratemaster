"""Celery worker entry point.

Run from backend directory:
  celery -A celery_worker worker -l info

On Windows (avoids billiard PermissionError):
  celery -A celery_worker worker -l info --pool=solo

With Redis at localhost:6379.
"""
from app.celery_app import celery_app

__all__ = ["celery_app"]
