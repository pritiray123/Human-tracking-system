from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import backend.config as config
from backend.api import feed, routes
from backend.camera.local import LocalCamera
from backend.devices.registry import registry
from backend.transport import ws_receiver


@asynccontextmanager
async def lifespan(app: FastAPI):
    local_cam = LocalCamera()
    if local_cam.open():
        registry.add(local_cam)
    else:
        print(
            "[HTS] WARNING: No local camera found.\n"
            "      Running in remote-only mode."
        )

    broadcaster_task = asyncio.create_task(feed.start_broadcaster())

    print("\n" + "=" * 56)
    print("  HTS — Multi-Device Camera Backend")
    print("=" * 56)
    print(f"  Backend API:      https://localhost:{config.BACKEND_PORT}")
    print(f"  Remote streamer:  {config.STREAMER_URL}")
    print(f"  Open React UI:    http://localhost:5173")
    print("=" * 56 + "\n")

    yield

    broadcaster_task.cancel()
    try:
        await broadcaster_task
    except asyncio.CancelledError:
        pass
    registry.release_all()
    print("[HTS] Backend shut down cleanly.")


app = FastAPI(title="HTS Backend", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router,      prefix="/api")
app.include_router(feed.router)
app.include_router(ws_receiver.router)


if __name__ == "__main__":
    import uvicorn
    from backend.certs import ensure_certificates
    cert_file, key_file = ensure_certificates(local_ip=config.LOCAL_IP)
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=config.BACKEND_PORT,
        reload=False,
    )

