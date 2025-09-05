FIFO Batch Processor
====================

What this project contains:
- main.py         : The FIFO processing client. Reads CSV, processes in batches of 50 by calling microservice.
- mock_server.py  : A simple mock microservice that randomly simulates pass/fail responses.
- sample_points.csv : Sample CSV data (9 rows); replace with your 45k CSV file.
- processor.log   : Generated at runtime when you run main.py
- flow_diagram.png: Flow diagram image illustrating the architecture.
- requirements.txt: Python dependencies.

How it works (short):
1. Load CSV into a deque (FIFO).
2. Repeatedly take up to 50 records from the left (head) of the FIFO.
3. Fire 50 concurrent POST requests to the microservice; await all responses.
4. Log PASS for 2xx responses; FAIL otherwise.
5. Append every processed record back to the end of the FIFO.
6. Repeat (either forever with --forever or for a fixed number of cycles).

Run mock server:
    python3 mock_server.py

Run processor (against mock server):
    python3 main.py --csv sample_points.csv --url http://127.0.0.1:8080/process --max-cycles 100

Run forever:
    python3 main.py --csv sample_points.csv --url http://127.0.0.1:8080/process --forever

Notes:
- For production, replace mock_server with your real microservice endpoint.
- Consider persistence for FIFO state if you need restart-resilience.
- Be careful: because items are re-appended, the system will run continuously; use max-cycles or other stop conditions if needed.
