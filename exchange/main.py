from fastapi import FastAPI, HTTPException
import random
import time

app = FastAPI(title="Exchange", version="1.0.0")

ERROR_FAIL_UNTIL = 0.0
ERROR_FAIL_PROB = 0.1
ERROR_FAIL_DURATION = 5.0

@app.get("/convert")
async def convert_currency():

    global ERROR_FAIL_UNTIL
    current_time = time.time()

    is_failing = False

    if current_time < ERROR_FAIL_UNTIL:
        is_failing = True

    elif random.random() < ERROR_FAIL_PROB:
        is_failing = True
        ERROR_FAIL_UNTIL = current_time + ERROR_FAIL_DURATION

    if is_failing:
        raise HTTPException(status_code = 503, detail="Simulação de erro por falha")

    exchange_rate = round(random.uniform(5.0, 6.0), 2)
    return {"exchange_rate": exchange_rate}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "Exchange"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
