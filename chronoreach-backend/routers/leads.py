import pandas as pd
from fastapi import APIRouter, File, UploadFile, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models import Lead

router = APIRouter(prefix="/api/leads", tags=["leads"])

INSIGHTS = {
    "Razorpay": "Just raised Series F — $160M",
    "Zepto": "Expanding to 100 cities by Q2 2026",
    "CRED": "Launched vehicle management feature",
    "Cashfree": "Launched instant bank verification API",
    "Juspay": "Processing 80M transactions/day",
    "AcmeSaaS": "Raised Series B — building AI-first CRM",
    "PhonePe": "Crossed 500M users — expanding to lending",
    "Groww": "Series E — launched mutual fund SIPs",
    "Meesho": "Series F — social commerce leader",
    "Slice": "Series B — Gen-Z neobank play",
    "BharatPe": "Series E — merchant payments network",
}

# Flexible field detection helpers
def _pick(row: dict, *keys):
    for k in keys:
        if k in row and row[k]:
            return row[k]
    return None

def _split_name(full_name: str):
    parts = (full_name or "").strip().split(None, 1)
    return (parts[0] if parts else ""), (parts[1] if len(parts) > 1 else "")

@router.post("/upload")
async def upload_leads(file: UploadFile = File(...)):
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file.file)
    else:
        df = pd.read_excel(file.file)
        
    columns = list(df.columns)
    email_col = next((c for c in columns if '@' in c or 'email' in c.lower()), None)
    
    preview = df.head(5).to_dict(orient="records")
    insights_found = 0
    
    company_col = next((c for c in columns if 'company' in c.lower() or 'org' in c.lower()), None)
    if company_col:
        for val in df[company_col].dropna():
            if val in INSIGHTS:
                insights_found += 1
                
    return {
        "columns_detected": columns,
        "email_col": email_col,
        "preview_rows": preview,
        "insights_found": insights_found
    }

@router.post("/confirm")
async def confirm_leads(payload: dict, db: AsyncSession = Depends(get_db)):
    """Accept leads from frontend — handles both old {rows, field_mapping} and new {leads} format."""
    rows = payload.get("leads") or payload.get("rows") or []
    
    saved = 0
    insights_cnt = 0
    
    for row in rows:
        # Flexible field detection
        email = _pick(row, "email_address", "email", "Email", "EMAIL", "email_id")
        if not email:
            continue
        
        full_name = _pick(row, "full_name", "Full Name", "Name", "name", "NAME")
        first_name, last_name = _split_name(full_name) if full_name else ("", "")
        if not first_name:
            first_name = _pick(row, "first_name", "First Name", "FirstName") or ""
        if not last_name:
            last_name = _pick(row, "last_name", "Last Name", "LastName") or ""
        
        company = _pick(row, "org", "company", "Company", "COMPANY", "Organization", "organisation")
        title = _pick(row, "job_title", "title", "Title", "JOB_TITLE", "designation", "Designation")
        funding = _pick(row, "funding_round", "Funding", "funding", "round")
        
        insight = INSIGHTS.get(company) if company else None
        if insight:
            insights_cnt += 1
        
        # Check if lead with this email already exists
        existing = await db.execute(select(Lead).where(Lead.email == email))
        if existing.scalar_one_or_none():
            saved += 1  # Count but skip duplicate
            continue
            
        db.add(Lead(
            email=email,
            company=company,
            first_name=first_name,
            last_name=last_name,
            title=title,
            linkedin_headline=funding,  # Store funding_round in linkedin_headline for now
            insight=insight,
            custom_fields=row
        ))
        saved += 1
        
    await db.commit()
    return {"saved_count": saved, "leads_with_insights": insights_cnt}

@router.get("")
async def list_leads(page: int = 1, limit: int = 20, search: str = "", db: AsyncSession = Depends(get_db)):
    offset = (page - 1) * limit
    stmt = select(Lead)
    if search:
        stmt = stmt.where(Lead.email.ilike(f"%{search}%") | Lead.company.ilike(f"%{search}%"))
    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    return res.scalars().all()
