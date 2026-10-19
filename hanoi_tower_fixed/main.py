"""하노이의 탑: 필요한 이동만 계산하는 FastAPI 서버."""
from pathlib import Path
import re

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

MAX_DISKS = 10000  # 필요하면 변경. 10000개까지 결과 계산 가능.
BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="하노이의 탑 애니메이션")
APP_VERSION = "2.1-fixed"
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def check_disk_count(n: int) -> None:
    if not 1 <= n <= MAX_DISKS:
        raise HTTPException(status_code=400, detail=f"원판 개수는 1~{MAX_DISKS:,}개여야 합니다.")


def calculate_move(n: int, step: int) -> dict:
    """전체 이동 목록을 만들지 않고 step번째 이동을 계산 (1부터 시작)."""
    disk = (step & -step).bit_length()
    previous = step >> disk
    direction = -1 if (n - disk) % 2 == 0 else 1
    source = (previous * direction) % 3
    return {"disk": disk, "from": source, "to": (source + direction) % 3}


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/config")
def config():
    return {"max_disks": MAX_DISKS, "max_visual_disks": 1000, "version": APP_VERSION}


@app.get("/api/hanoi/{n}")
def hanoi_info(n: int):
    check_disk_count(n)
    return {"n": n, "total_moves": str((1 << n) - 1)}


@app.get("/api/hanoi/{n}/moves")
def hanoi_moves(n: int, start: str = "1", limit: int = Query(default=100, ge=1, le=200)):
    check_disk_count(n)
    # 10000개 원판의 전체 이동 횟수는 약 3011자리.
    if not re.fullmatch(r"[1-9][0-9]{0,3100}", start):
        raise HTTPException(status_code=400, detail="올바른 시작 이동 번호가 아닙니다.")
    start_number = int(start)
    total = (1 << n) - 1
    if start_number > total:
        return {"moves": [], "next_start": str(start_number)}
    end = min(start_number + limit, total + 1)
    moves = [calculate_move(n, k) for k in range(start_number, end)]
    return {"moves": moves, "next_start": str(end)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
