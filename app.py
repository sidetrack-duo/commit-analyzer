from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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
    latest: Optional[datetime]
    weekly: int
    mostActiveDay: Optional[str]

# ai DTO
class AiSummaryRequest(BaseModel):
    projectId: int
    messages:List[str]

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

# ai
@app.post("/analyze/ai-summary")
def analyze_ai_summary(req: AiSummaryRequest):
    if not req.messages :
         return {"summary" : "커밋 기반 데이터가 없습니다."}
     
    prompt = f"""
    다음 커밋 메시지를 기반으로 개발 활동을 요약해줘.

    {req.messages}
    형식 : 
    - 주요 작업
    - 주요 키워드 
    - 개발 특징
    """

    response = client.chat.completions.create(
        model= "gpt-4.1-mini",
        messages=[
            {"role": "system", "content": "너는 개발 활동을 요약하는 AI야."},
            {"role": "user", "content": prompt} 
        ]
    )

    return {
        "summary" : response.choices[0].message.content
    }