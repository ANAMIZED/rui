"""RUI FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from rui import __version__
from rui.api.routes import router

app = FastAPI(
    title="RUI — Recursive UltraIntelligence",
    description=(
        "Autonomous Agentic Operating System API. "
        "Recursive call trees, cost kernels, governance, promotion gates, multi-agent workflows."
    ),
    version=__version__,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "rui", "version": __version__}


def run():
    import uvicorn
    uvicorn.run("rui.api.main:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    run()
