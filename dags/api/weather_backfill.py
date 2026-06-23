import sys
import logging
from pathlib import Path

# ============================================================
# Add the dags folder to the Python path
# So it can find weather_extract when run locally
# ============================================================
sys.path.insert(0, str(Path(__file__).parent.parent))

from api.weather_extract import backfill_historical

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s"
)
log = logging.getLogger(__name__)


if __name__ == "__main__":
    sample_mode = "--sample" in sys.argv

    if sample_mode:
        log.info("SAMPLE MODE — fetching 3 municipalities, last 90 days")
        path = backfill_historical(days=90, sample_size=3)
    else:
        log.info("FULL MODE — fetching all 257 municipalities, last 90 days")
        path = backfill_historical(days=90)

    log.info(f"Backfill complete — output: {path}")