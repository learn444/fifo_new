from aiohttp import web
import random
import json

async def handle_root(request):
    return web.Response(
        text="🚀 Mock Microservice is running! Use POST /process to send data.",
        content_type="text/plain"
    )

async def handle_process(request):
    try:
        data = await request.json()
    except Exception:
        return web.Response(text="Invalid JSON", status=400)

    # Randomly simulate pass/fail for demo
    if random.random() > 0.2:
        return web.json_response({"status": "success", "id": data.get("id")}, status=200)
    else:
        return web.json_response({"status": "error", "id": data.get("id")}, status=500)

def create_app():
    app = web.Application()
    app.router.add_get("/", handle_root)          # ✅ Root endpoint
    app.router.add_post("/process", handle_process)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host="127.0.0.1", port=5000)
