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
