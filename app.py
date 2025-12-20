from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from collections import Counter

app = FastAPI()

#  Request DTO 
class CommitItem(BaseModel):
    sha: str
    date: datetime
    message: str

class CommitAnalyzeRequest(BaseModel):
    projectId: int
    commits: List[CommitItem]

#  Response DTO 
class CommitSummaryResponse(BaseModel):
    total: int
    latest: datetime | None
    weekly: int
    mostActiveDay: str | None

# 커밋 통계
@app.post("/analyze/summary", response_model=CommitSummaryResponse)
def analyze_summary(req: CommitAnalyzeRequest):
    commits = req.commits

    if not commits:
        return CommitSummaryResponse(
            total=0,
            latest=None,
            weekly=0,
            mostActiveDay=None
        )

    total = len(commits)
    latest = max(c.date for c in commits)

    start_of_week = datetime.now() - timedelta(days=datetime.now().weekday())
    weekly = len([c for c in commits if c.date >= start_of_week])

    counter = Counter(c.date.strftime("%A").upper() for c in commits)
    most_active_day = counter.most_common(1)[0][0]

    return CommitSummaryResponse(
        total=total,
        latest=latest,
        weekly=weekly,
        mostActiveDay=most_active_day
    )


# 주간 커밋 
class WeeklyAnalyzeRequest(BaseModel):
    projectId: int
    commitDates: List[datetime]


class WeeklyCommitCount(BaseModel):
    weekday: int   # 1(Monday) ~ 7(Sunday)
    count: int


@app.post("/analyze/weekly", response_model=List[WeeklyCommitCount])
def analyze_weekly(req: WeeklyAnalyzeRequest):
    counter = Counter()

    for d in req.commitDates:
        counter[d.weekday() + 1] += 1

    return [
        # monday = 1
        WeeklyCommitCount(weekday=k, count=v)
        for k, v in sorted(counter.items())
    ]

# 6개월 커밋 히스토리 
class HistoryAnalyzeRequest(BaseModel):
    projectId: int
    commitDates: List[datetime]


class MonthlyCommitCount(BaseModel):
    yearMonth: str   # e.g. "2025-09"
    count: int


@app.post("/analyze/history", response_model=List[MonthlyCommitCount])
def analyze_history(req: HistoryAnalyzeRequest):
    counter = Counter()

    now = datetime.now()
    six_months_ago = now - timedelta(days=180)

    for d in req.commitDates:
        if d < six_months_ago:
            continue

        key = d.strftime("%Y-%m")
        counter[key] += 1

    return [
        MonthlyCommitCount(yearMonth=k, count=v)
        for k, v in sorted(counter.items())
    ]