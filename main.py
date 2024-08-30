from fastapi import FastAPI, Request
from starlette.responses import RedirectResponse, JSONResponse, HTMLResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.middleware import SlowAPIMiddleware
import socket
import struct
import time
import subprocess
import re

app = FastAPI()

# Initialize the Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(429, _rate_limit_exceeded_handler)

# Add SlowAPI Middleware
app.add_middleware(SlowAPIMiddleware)

def request_time_from_ntp(addr='localhost'):
    REF_TIME_1970 = 2208988800  # Reference time
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = b'\x1b' + 47 * b'\0'
    client.sendto(data, (addr, 123))
    data, address = client.recvfrom(1024)
    if data:
        t = struct.unpack('!12I', data)[10]
        t -= REF_TIME_1970
    return time.ctime(t), t

def parse_tracking_output(output):
    tracking_data = {}
    for line in output.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            tracking_data[key.strip()] = value.strip()
    return tracking_data

def parse_sources_csv_output(output):
    lines = output.split("\n")
    sources = []
    headers = ["Mode", "Name/IP address", "Stratum", "Poll", "Reach", "LastRx", "Last sample"]
    
    for line in lines[3:]:  # Skip the first three lines which are the header and separator
        if not line.strip():
            continue
        # Extract Mode
        mode = line[:2].strip()
        # Split the rest of the line by whitespace
        parts = re.split(r'\s{2,}', line[2:].strip())
        
        if len(parts) >= len(headers) - 1:
            # Ensure that we have all the parts and join any remaining parts for "Last sample"
            main_parts = parts[:len(headers) - 2]
            last_sample = " ".join(parts[len(headers) - 2:])
            source_data = dict(zip(headers[1:-1], main_parts))
            source_data["Last sample"] = last_sample
            source_data["Mode"] = mode
            sources.append(source_data)
    
    return sources

#@app.get("/", include_in_schema=False)
#async def root():
#    return RedirectResponse(url="/docs")

@app.get("/", include_in_schema=False)
async def root():
    with open("index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.get("/ntp")
@limiter.limit("10/second")
async def get_ntp_time(request: Request):
    formatted_time, timestamp = request_time_from_ntp()
    return {
        "ntp_server": "time.jpaul.io",
        "timestamp": timestamp,
        "formatted_time": formatted_time
    }

@app.get("/chrony/tracking")
@limiter.limit("1/second")
async def get_chrony_tracking(request: Request):
    result = subprocess.run(["chronyc", "tracking"], capture_output=True, text=True)
    tracking_data = parse_tracking_output(result.stdout)
    return tracking_data

@app.get("/chrony/sources")
@limiter.limit("1/second")
async def get_chrony_sources(request: Request):
    result = subprocess.run(["chronyc", "sources", "-c"], capture_output=True, text=True)
    sources_data = parse_sources_csv_output(result.stdout)
    return sources_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
