import sqlite3
import uuid
from datetime import datetime, UTC
from enum import Enum

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os

app = FastAPI()

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/campaigns.db", check_same_thread=False)
conn.cursor().execute("""
    CREATE TABLE IF NOT EXISTS campaigns (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        budget REAL NOT NULL,
        status TEXT NOT NULL,
        createdAt TEXT NOT NULL
    )
""")

conn.commit()


class StatusEnum(str, Enum):
    active = "active"
    paused = "paused"


class CampaignCreate(BaseModel):
    name: str
    budget: float
    status: StatusEnum


class Campaign(CampaignCreate):
    id: str
    createdAt: str


@app.get("/campaigns", response_model=list[Campaign])
def get_campaigns():
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, budget, status, createdAt FROM campaigns")
    rows = cursor.fetchall()
    return [
        Campaign(id=row[0], name=row[1], budget=row[2], status=row[3], createdAt=row[4])
        for row in rows
    ]


@app.post("/campaign", response_model=Campaign)
def create_campaign(campaign: CampaignCreate):
    campaign_id = str(uuid.uuid4())
    created_at = datetime.now(UTC).isoformat()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO campaigns (id, name, budget, status, createdAt) VALUES (?, ?, ?, ?, ?)",
        (campaign_id, campaign.name, campaign.budget, campaign.status, created_at),
    )
    conn.commit()
    return Campaign(
        id=campaign_id,
        name=campaign.name,
        budget=campaign.budget,
        status=campaign.status,
        createdAt=created_at,
    )


@app.put("/campaign/{campaign_id}", response_model=Campaign)
def update_campaign(campaign_id: str, campaign: CampaignCreate):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM campaigns WHERE id=?", (campaign_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    cursor.execute(
        "UPDATE campaigns SET name=?, budget=?, status=? WHERE id=?",
        (campaign.name, campaign.budget, campaign.status, campaign_id),
    )
    conn.commit()
    cursor.execute(
        "SELECT id, name, budget, status, createdAt FROM campaigns WHERE id=?",
        (campaign_id,),
    )
    row = cursor.fetchone()
    return Campaign(
        id=row[0], name=row[1], budget=row[2], status=row[3], createdAt=row[4]
    )


@app.delete("/campaign/{campaign_id}")
def delete_campaign(campaign_id: str):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM campaigns WHERE id=?", (campaign_id,))
    if cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    cursor.execute("DELETE FROM campaigns WHERE id=?", (campaign_id,))
    conn.commit()
    return {"detail": "Campaign deleted"}
