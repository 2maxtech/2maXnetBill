from fastapi import FastAPI

from agent.api.pppoe import router as pppoe_router
from agent.api.system import router as system_router

app = FastAPI(title="2maXnetBill Gateway Agent")

app.include_router(pppoe_router)
app.include_router(system_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gateway-agent"}
