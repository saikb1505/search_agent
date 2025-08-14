# models/schemas.py
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, ConfigDict
from datetime import datetime

class PeopleItem(BaseModel):
    # Common columns (optional) from your example schema
    id: int
    search_id: Optional[int] = None
    google_result_id: Optional[int] = None
    person_uuid: Optional[str] = None
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    title: Optional[str] = None
    headline: Optional[str] = None
    person_industry: Optional[str] = None
    image_url: Optional[str] = None
    person_city: Optional[str] = None
    person_state: Optional[str] = None
    person_country_code: Optional[str] = None
    person_country: Optional[str] = None
    person_region: Optional[str] = None

    org_uuid: Optional[str] = None
    org_name: Optional[str] = None
    org_website: Optional[str] = None
    org_domain: Optional[str] = None
    org_linkedin_url: Optional[str] = None
    org_employees: Optional[int] = None
    org_industry: Optional[str] = None
    org_city: Optional[str] = None
    org_state: Optional[str] = None
    org_country_code: Optional[str] = None
    org_country: Optional[str] = None
    org_region: Optional[str] = None

    emails_json: Optional[Any] = None
    phones_json: Optional[Any] = None
    raw_json: Optional[Any] = None

    created_at: Optional[datetime] = None

    # Allow any extra columns your table may have
    model_config = ConfigDict(extra="allow")

class PeopleSearchResponse(BaseModel):
    q: Optional[str] = None
    search_id: Optional[int] = None
    tech_stack: List[str] = []
    locations: List[str] = []
    sort: Literal["recent", "name"] = "recent"
    limit: int
    offset: int
    count: int
    items: List[PeopleItem]
