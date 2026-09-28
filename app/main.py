from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.encoders import router as encoders_router
from app.api.decoders import router as decoders_router
from app.api.multiview import router as multiview_router

app = FastAPI(title="BB Stream Gateway", version="0.4.0")

app.include_router(encoders_router)
app.include_router(decoders_router)
app.include_router(multiview_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse("/encoder")


@app.get("/encoder", include_in_schema=False)
def encoder_page():
    return FileResponse("app/static/encoder.html")


@app.get("/decoder", include_in_schema=False)
def decoder_page():
    return FileResponse("app/static/decoder.html")


@app.get("/catalogo", include_in_schema=False)
def catalog_page():
    return FileResponse("app/static/catalogo.html")

@app.get("/multiview", include_in_schema=False)
def multiview_page():
    return FileResponse("app/static/multiview.html")

@app.get("/api/health")
def health():
    return {
        "status": "online",
        "application": "BB Stream Gateway",
        "version": "0.4.0"
    }


