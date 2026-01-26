import asyncio

from fastapi import FastAPI, Request
import itertools
import uvicorn
from fastapi.params import Form

app = FastAPI()

# 500 per day
dhl_token = [
    # "REDACTED",
    # "REDACTED",
    # "REDACTED",
    # "REDACTED",
    # "REDACTED",
    # "REDACTED",
]
dhl_cycle = itertools.cycle(dhl_token)

# 300 per day
yelp_token = [
    # "<REDACTED>",
    # "<REDACTED>",
    # "<REDACTED>",
    # "<REDACTED>",
    # "<REDACTED>",
    # "<REDACTED>",
    # "<REDACTED>",
    # "<REDACTED>",
    # "<REDACTED>",
    # "<REDACTED>",
]
yelp_cycle = itertools.cycle(yelp_token)


@app.middleware("http")
async def log_failed_requests(request: Request, call_next):
    """
    Middleware: uniformly print all requests with status code >= 400
    """
    response = await call_next(request)

    if response.status_code >= 400:
        # Get request body (usually empty for GET, present for POST/PUT)
        body_bytes = await request.body()
        body_text = body_bytes.decode("utf-8") if body_bytes else ""

        print("==== FAILED REQUEST ====")
        print("Method:", request.method)
        print("URL:", request.url)
        print("Status code:", response.status_code)
        print("Headers:", dict(request.headers))
        print("Query params:", dict(request.query_params))
        print("Body:", body_text)
        print("========================")

    return response

cycle_lock = asyncio.Lock()
cycle_lock_yelp = asyncio.Lock()


@app.post("/dhl")
async def get_next_item(name: str = Form(...)):
    async with cycle_lock:
        token = next(dhl_cycle)
    return {"access_token": token}

@app.post("/yelp")
async def get_yelp_token(name: str = Form(...)):
    async with cycle_lock_yelp:
        token = next(yelp_cycle)
    return {"access_token": token}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
