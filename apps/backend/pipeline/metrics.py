import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional

from config import settings

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False
    psutil = None


class JsonFormatter(logging.Formatter):
    def format(self, record):
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in (
            "stage",
            "demo_mode",
            "sample_rows",
            "seed",
            "poisson_mean",
            "duration_seconds",
            "model",
            "metrics",
            "hyperparameters",
            "schema_version",
        ):
            if hasattr(record, key):
                payload[key] = getattr(record, key)
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def configure_logging():
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)
    formatter = JsonFormatter() if settings.LOG_JSON else logging.Formatter(settings.LOG_FORMAT)
    handlers = [logging.StreamHandler()]
    handlers[0].setFormatter(formatter)
    file_handler = RotatingFileHandler(
        settings.LOG_DIR / settings.LOG_FILENAME,
        maxBytes=settings.LOG_MAX_BYTES,
        backupCount=settings.LOG_BACKUP_COUNT,
    )
    file_handler.setFormatter(formatter)
    handlers.append(file_handler)
    logging.basicConfig(
        level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
        handlers=handlers,
        force=True,
    )


@dataclass
class StageMetric:
    stage: str
    duration_seconds: float
    records_in: Optional[int] = None
    records_out: Optional[int] = None


@dataclass
class PipelineMetrics:
    timestamp: str = ""
    demo_mode: bool = False
    total_duration_seconds: float = 0.0
    stages: list = field(default_factory=list)
    records_initial: int = 0
    records_final: int = 0
    reduction_pct: float = 0.0
    completeness_pct: float = 100.0
    outliers_detected: int = 0
    warnings_count: int = 0
    peak_memory_mb: float = 0.0
    avg_cpu_percent: float = 0.0

    def to_dict(self):
        return {
            "schema_version": settings.METRICS_SCHEMA_VERSION,
            "timestamp": self.timestamp,
            "demo_mode": self.demo_mode,
            "total_duration_seconds": round(self.total_duration_seconds, 2),
            "stages": [
                {
                    "stage": s.stage,
                    "duration_seconds": round(s.duration_seconds, 2),
                    "records_in": s.records_in,
                    "records_out": s.records_out,
                }
                for s in self.stages
            ],
            "records_initial": self.records_initial,
            "records_final": self.records_final,
            "reduction_pct": round(self.reduction_pct, 1),
            "completeness_pct": round(self.completeness_pct, 1),
            "outliers_detected": self.outliers_detected,
            "warnings_count": self.warnings_count,
            "peak_memory_mb": round(self.peak_memory_mb, 1),
            "avg_cpu_percent": round(self.avg_cpu_percent, 1),
        }

    def summary(self) -> str:
        lines = [
            "=" * 70,
            "RESUMEN DE KPIs - PIPELINE DATAOPS",
            "=" * 70,
            f"  Ejecucion:       {self.timestamp}",
            f"  Modo:            {'Demo' if self.demo_mode else 'Produccion'}",
            f"  Duracion total:  {self.total_duration_seconds:.2f} seg",
        ]
        for s in self.stages:
            dur = f"{s.duration_seconds:.2f}s"
            rec = ""
            if s.records_in is not None and s.records_out is not None:
                rec = f"  [{s.records_in} > {s.records_out}]"
            lines.append(f"    - {s.stage}: {dur}{rec}")
        lines.extend(
            [
                f"  Registros:        {self.records_initial} > {self.records_final}"
                f" ({self.reduction_pct:.1f}% reduccion)",
                f"  Completitud:      {self.completeness_pct}%",
                f"  Outliers:         {self.outliers_detected}",
                f"  Advertencias:     {self.warnings_count}",
                f"  RAM pico:         {self.peak_memory_mb:.1f} MB",
                f"  CPU promedio:     {self.avg_cpu_percent:.1f}%",
                "=" * 70,
            ]
        )
        return "\n".join(lines)


class MetricsCollector:
    def __init__(self):
        self.metrics = PipelineMetrics(timestamp=datetime.now(timezone.utc).isoformat())
        self._start_time = time.time()
        self._stage_start = None
        self._current_stage = None
        self._warnings_before = 0
        self._process = psutil.Process() if HAS_PSUTIL else None
        self._cpu_samples: list[float] = []
        self._peak_memory = 0.0
        if self._process:
            self._process.cpu_percent(interval=None)  # warm-up

    def _sample_resources(self):
        if not self._process:
            return
        try:
            mem = self._process.memory_info().rss / (1024 * 1024)
            cpu = self._process.cpu_percent(interval=None)
            if mem > self._peak_memory:
                self._peak_memory = mem
            self._cpu_samples.append(cpu)
        except Exception:
            pass

    def set_demo_mode(self, enabled: bool):
        self.metrics.demo_mode = enabled

    def start_stage(self, name: str, records_in: int = None):
        self._sample_resources()
        self._current_stage = StageMetric(
            stage=name,
            duration_seconds=0.0,
            records_in=records_in,
        )
        self._stage_start = time.time()

    def end_stage(self, records_out: int = None):
        if self._current_stage and self._stage_start:
            self._current_stage.duration_seconds = time.time() - self._stage_start
            if records_out is not None:
                self._current_stage.records_out = records_out
            self.metrics.stages.append(self._current_stage)
        self._current_stage = None
        self._stage_start = None
        self._sample_resources()

    def set_records(self, initial: int, final: int):
        self.metrics.records_initial = initial
        self.metrics.records_final = final
        if initial > 0:
            self.metrics.reduction_pct = (1 - final / initial) * 100

    def set_completeness(self, pct: float):
        self.metrics.completeness_pct = pct

    def set_outliers(self, count: int):
        self.metrics.outliers_detected = count

    def set_warnings(self, count: int):
        self.metrics.warnings_count = count

    def finalize(self):
        self.metrics.total_duration_seconds = time.time() - self._start_time
        self._sample_resources()
        self.metrics.peak_memory_mb = self._peak_memory
        samples = [c for c in self._cpu_samples if c > 0]
        self.metrics.avg_cpu_percent = sum(samples) / len(samples) if samples else 0.0
        return self.metrics

    def save(self, metrics_dir: Path = None):
        if metrics_dir is None:
            metrics_dir = settings.METRICS_DIR
        metrics_dir.mkdir(parents=True, exist_ok=True)
        path = metrics_dir / "pipeline_metrics.jsonl"
        with open(path, "a") as f:
            f.write(json.dumps(self.metrics.to_dict()) + "\n")
        return path
