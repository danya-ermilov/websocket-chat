import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from app.websocket_manager import ConnectionManager
from app.redis_manager import RedisManager
from app.background_tasks import start_decrement_task
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

app = FastAPI()

templates = Jinja2Templates(directory="templates")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_homepage(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

redis_manager = RedisManager()
manager = ConnectionManager()

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(start_decrement_task(redis_manager, manager))

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    client_ip = websocket.client.host

    try:
        current_messages = await redis_manager.get_messages()
        await websocket.send_text(current_messages)

        while True:
            data = await websocket.receive_text()
            await redis_manager.add_message(client_ip, data)

            messages = await redis_manager.get_messages()
            await manager.broadcast(messages)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)

