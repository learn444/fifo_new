import asyncio
import aiohttp
import logging
import argparse
import csv
import platform
from collections import deque
from datetime import datetime

# Configuration
BATCH_SIZE = 50
LOG_FILE = "processor.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler(LOG_FILE), logging.StreamHandler()]
)

async def call_microservice(session, url, record, timeout=10):
    try:
        async with session.post(url, json=record, timeout=timeout) as resp:
            text = await resp.text()
            status = resp.status
            passed = 200 <= status < 300
            return passed, status, text
    except Exception as e:
        return False, None, str(e)

async def process_batch(fifo: deque, url: str, cycle_id: int):
    batch = []
    for _ in range(min(BATCH_SIZE, len(fifo))):
        batch.append(fifo.popleft())

    if not batch:
        logging.info("FIFO empty, nothing to process.")
        return

    async with aiohttp.ClientSession() as session:
        tasks = [call_microservice(session, url, rec) for rec in batch]
        results = await asyncio.gather(*tasks)

    for rec, res in zip(batch, results):
        passed, status, info = res
        if passed:
            logging.info(f"PASS id={rec.get('id')} status={status}")
        else:
            logging.error(f"FAIL id={rec.get('id')} status={status} info={info}")
        fifo.append(rec)

    logging.info(f"Completed cycle {cycle_id}: processed {len(batch)} records. FIFO size now {len(fifo)}")

async def worker_loop(fifo: deque, url: str, run_forever: bool, max_cycles: int):
    cycle = 0
    try:
        while True:
            cycle += 1
            await process_batch(fifo, url, cycle)
            if not run_forever and cycle >= max_cycles:
                logging.info("Reached max cycles. Exiting.")
                break
            await asyncio.sleep(0.1)
    except asyncio.CancelledError:
        logging.info("Worker loop cancelled, exiting cleanly.")

def load_csv_to_fifo(csv_path: str):
    fifo = deque()
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fifo.append(dict(row))
    return fifo

def main():
    parser = argparse.ArgumentParser(description="FIFO batch processor")
    parser.add_argument("--csv", default="sample_points.csv", help="Input CSV")
    parser.add_argument("--url", default="http://127.0.0.1:5000/process", help="Microservice URL")
    parser.add_argument("--max-cycles", type=int, default=10, help="Max cycles to run (ignored if --forever)")
    parser.add_argument("--forever", action="store_true", help="Run forever")
    args = parser.parse_args()

    fifo = load_csv_to_fifo(args.csv)
    logging.info(f"Loaded {len(fifo)} records into FIFO")

    # ✅ Fix for Windows event loop
    if platform.system() == "Windows":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    try:
        asyncio.run(worker_loop(fifo, args.url, args.forever, args.max_cycles))
    except KeyboardInterrupt:
        logging.info("Process interrupted by user.")
    finally:
        now = datetime.utcnow().isoformat()
        logging.info(f"Shutting down at {now}. FIFO size: {len(fifo)}")

if __name__ == '__main__':
    main()
