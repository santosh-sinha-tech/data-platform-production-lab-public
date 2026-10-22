"""Pure validation, statistics, and economic calculations."""
from dataclasses import dataclass
from pathlib import Path
import math
import statistics

@dataclass(frozen=True)
class Config:
    rows: int = 60000
    seed: int = 42
    partitions: int = 4
    fragmented_files: int = 48
    compacted_files: int = 4
    warmups: int = 1
    iterations: int = 5
    cores: int = 2
    partitioned: bool = True
    compute_hour_cost: float = 0.0
    compaction_seconds: float | None = None

    def validate(self) -> None:
        for key in ("rows", "partitions", "fragmented_files", "compacted_files", "warmups", "iterations", "cores"):
            value = getattr(self, key)
            if type(value) is not int or value < 1:
                raise ValueError(f"{key} must be a positive integer")
        if type(self.seed) is not int or type(self.partitioned) is not bool:
            raise ValueError("seed must be integer and partitioned boolean")
        if self.iterations < 3 or self.fragmented_files <= self.compacted_files:
            raise ValueError("need >=3 measured iterations and fragmented_files > compacted_files")
        if self.rows < max(self.partitions, self.fragmented_files):
            raise ValueError("rows must cover partition and target file counts")
        if self.partitioned and (self.fragmented_files % self.partitions or self.compacted_files % self.partitions):
            raise ValueError("partitioned file targets must be multiples of partitions")
        if self.compute_hour_cost is None:
            raise ValueError("compute_hour_cost must be supplied as a number, default zero")
        for value in (self.compute_hour_cost, self.compaction_seconds):
            if value is not None and (isinstance(value, bool) or not math.isfinite(value) or value < 0):
                raise ValueError("cost and compaction time must be finite and nonnegative")

def summarize(samples: list[float]) -> dict:
    if len(samples) < 3 or any(not math.isfinite(x) or x <= 0 for x in samples):
        raise ValueError("invalid benchmark samples")
    q = statistics.quantiles(samples, n=4, method="inclusive")
    return {"median_seconds": statistics.median(samples), "min_seconds": min(samples),
            "max_seconds": max(samples), "iqr_seconds": q[2]-q[0], "samples_seconds": samples}

def file_stats(path: Path) -> dict:
    files = sorted(path.rglob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"no parquet files: {path}")
    sizes = [f.stat().st_size for f in files]
    return {"files": len(files), "parquet_bytes": sum(sizes), "min_file_bytes": min(sizes),
            "median_file_bytes": statistics.median(sizes), "max_file_bytes": max(sizes),
            "all_file_bytes": sum(f.stat().st_size for f in path.rglob("*") if f.is_file())}

def break_even(compaction: float, fragmented: float, compacted: float, rate: float) -> dict:
    if any(not math.isfinite(x) or x < 0 for x in (compaction, fragmented, compacted, rate)):
        raise ValueError("model inputs must be finite and nonnegative")
    savings = fragmented - compacted
    return {"saved_seconds_per_read": savings, "compaction_compute_cost": compaction*rate/3600,
            "saved_compute_cost_per_read": savings*rate/3600,
            "break_even_reads": math.ceil(compaction/savings) if savings > 0 else None,
            "cost_break_even_reads": math.ceil(compaction/savings) if savings > 0 and rate > 0 else None,
            "rate_per_compute_hour": rate}
