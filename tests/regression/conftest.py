"""
Regression Test Configuration

Provides shared fixtures and constants for regression tests.
"""

# Bandwidth thresholds for regression tests (GB/s per channel)
BANDWIDTH_THRESHOLDS = {
    'sequential': {
        'min': 100.0,   # Minimum expected bandwidth for sequential
        'target': 150.0, # Target bandwidth
        'max': 200.0,   # Maximum expected (sanity check)
    },
    'random': {
        'min': 50.0,
        'target': 80.0,
        'max': 120.0,
    },
    'stride': {
        'min': 60.0,
        'target': 100.0,
        'max': 150.0,
    },
}

# Latency thresholds (cycles)
LATENCY_THRESHOLDS = {
    'sequential': {
        'max_avg': 20.0,
        'max_p99': 50.0,
    },
    'random': {
        'max_avg': 50.0,
        'max_p99': 100.0,
    },
}

# Row hit rate thresholds (%)
ROW_HIT_THRESHOLDS = {
    'sequential': {'min': 50.0},
    'hotspot': {'min': 70.0},
    'random': {'min': 0.0},  # Random should have low row hits
}

# Power thresholds (mW per channel)
POWER_THRESHOLDS = {
    'active_max': 500.0,
    'idle_max': 50.0,
    'read_max': 450.0,
    'write_max': 420.0,
}

# Test configuration
REGRESSION_CONFIG = {
    'simulation_time_us': 100.0,
    'warmup_time_us': 10.0,
    'num_iterations': 3,
    'confidence_level': 0.95,
}
