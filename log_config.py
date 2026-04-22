# ==================================================
# log_config.py
# Suppress noisy third-party loggers
# Import this at the TOP of Vivie.py before anything else:
#   from log_config import suppress_noise
#   suppress_noise()
# ==================================================

import logging
import warnings

def suppress_noise():
    """Silence noisy third-party library logs."""

    noisy_loggers = [
        "httpx",
        "httpcore",
        "sentence_transformers",
        "chromadb",
        "chromadb.telemetry",
        "opentelemetry",
        "websockets",
        "websockets.server",
        "comtypes",
        "comtypes.client",
        "comtypes.client._code_cache",
        "urllib3",
        "asyncio",
    ]

    for name in noisy_loggers:
        logging.getLogger(name).setLevel(logging.ERROR)

    # Suppress DeprecationWarnings from third-party packages
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    # Keep Vivie's own logs clean but visible
    logging.basicConfig(
        level  = logging.WARNING,
        format = "[%(name)s] %(message)s"
    )

    print("🔇 Noisy loggers silenced.")
