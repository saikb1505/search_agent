# db/salesql_results.py
from typing import List, Dict, Any, Optional, Set
import json
import aiomysql
from db.async_mysql import get_db_connection

TABLE_GOOGLE_RESULTS = "google_search_results"
TABLE_SALESQL_RESULTS = "salesql_enriched_people"


def _looks_like_profile(url: str) -> bool:
    u = (url or "").lower()
    return "linkedin.com/in" in u


async def get_linkedin_urls_for_search_id(search_id: int) -> List[Dict[str, Any]]:
    conn = await get_db_connection()
    rows: List[Dict[str, Any]] = []
    async with conn.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            f"""
            SELECT id, link
            FROM {TABLE_GOOGLE_RESULTS}
            WHERE search_id = %s
              AND link LIKE '%%linkedin.com/in%%'
            """,
            (search_id,),
        )
        for r in await cursor.fetchall():
            if _looks_like_profile(r.get("link")):
                rows.append({"id": r["id"], "link": r["link"]})
    conn.close()
    return rows


async def get_existing_linkedin_urls(search_id: int) -> Set[str]:
    conn = await get_db_connection()
    urls: Set[str] = set()
    async with conn.cursor(aiomysql.DictCursor) as cursor:
        await cursor.execute(
            f"SELECT linkedin_url FROM {TABLE_SALESQL_RESULTS} WHERE search_id = %s",
            (search_id,),
        )
        for r in await cursor.fetchall():
            urls.add(r["linkedin_url"])
    conn.close()
    return urls


def _get_nested(d: Dict[str, Any], *path: str) -> Optional[Any]:
    cur: Any = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return None
        cur = cur[key]
    return cur


def _scalar_or_none(v: Any) -> Optional[Any]:
    """Return v if it's a safe SQL scalar, else None."""
    if v is None:
        return None
    if isinstance(v, (str, int, float)):
        return v
    # bool is int-like but can be surprising: treat as int 0/1
    if isinstance(v, bool):
        return int(v)
    # dict/list etc. -> None (raw will be in raw_json anyway)
    return None


def _to_int(v: Any) -> Optional[int]:
    """Best-effort convert to int; supports strings and dicts like {'value': 200} or {'max': 200}."""
    if v is None:
        return None
    if isinstance(v, bool):
        return int(v)
    if isinstance(v, (int, float)):
        try:
            return int(v)
        except Exception:
            return None
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        if s.isdigit():
            return int(s)
        return None
    if isinstance(v, dict):
        for k in ("value", "max", "min", "approx"):
            if k in v:
                try:
                    return int(v[k])
                except Exception:
                    continue
        return None
    return None


async def save_salesql_person(
    search_id: int,
    source_row_id: Optional[int],
    linkedin_url: str,
    payload: Dict[str, Any],
) -> None:
    """
    Insert/update a SalesQL person row mapped to SalesQL schema.
    This function sanitizes non-scalar fields to avoid MySQL param errors.
    """
    # ---- sanitize & map ----
    person_uuid = _scalar_or_none(payload.get("uuid"))
    first_name = _scalar_or_none(payload.get("first_name"))
    last_name = _scalar_or_none(payload.get("last_name"))
    full_name = _scalar_or_none(payload.get("full_name"))
    title = _scalar_or_none(payload.get("title"))
    headline = _scalar_or_none(payload.get("headline"))
    person_industry = _scalar_or_none(payload.get("industry"))
    image_url = _scalar_or_none(payload.get("image"))

    person_city = _scalar_or_none(_get_nested(payload, "location", "city"))
    person_state = _scalar_or_none(_get_nested(payload, "location", "state"))
    person_country_code = _scalar_or_none(_get_nested(payload, "location", "country_code"))
    person_country = _scalar_or_none(_get_nested(payload, "location", "country"))
    person_region = _scalar_or_none(_get_nested(payload, "location", "region"))

    org = payload.get("organization") or {}
    org_uuid = _scalar_or_none(org.get("uuid"))
    org_name = _scalar_or_none(org.get("name"))
    org_website = _scalar_or_none(org.get("website"))
    org_domain = _scalar_or_none(org.get("website_domain"))
    org_linkedin_url = _scalar_or_none(org.get("linkedin_url"))
    org_employees = _to_int(org.get("number_of_employees"))
    org_industry = _scalar_or_none(org.get("industry"))

    org_city = _scalar_or_none(_get_nested(org, "location", "city"))
    org_state = _scalar_or_none(_get_nested(org, "location", "state"))
    org_country_code = _scalar_or_none(_get_nested(org, "location", "country_code"))
    org_country = _scalar_or_none(_get_nested(org, "location", "country"))
    org_region = _scalar_or_none(_get_nested(org, "location", "region"))

    emails = payload.get("emails")
    phones = payload.get("phones")

    # ---- SQL assembled safely in one f-string ----
    sql_insert = f"""
INSERT INTO {TABLE_SALESQL_RESULTS}
( search_id, google_result_id, linkedin_url,
  person_uuid, full_name, first_name, last_name,
  title, headline, person_industry, image_url,
  person_city, person_state, person_country_code, person_country, person_region,
  org_uuid, org_name, org_website, org_domain, org_linkedin_url, org_employees, org_industry,
  org_city, org_state, org_country_code, org_country, org_region,
  emails_json, phones_json, raw_json )
VALUES (
  %s, %s, %s,
  %s, %s, %s, %s,
  %s, %s, %s, %s,
  %s, %s, %s, %s, %s,
  %s, %s, %s, %s, %s, %s, %s,
  %s, %s, %s, %s, %s,
  %s, %s, %s
)
ON DUPLICATE KEY UPDATE
  person_uuid = VALUES(person_uuid),
  full_name = VALUES(full_name),
  first_name = VALUES(first_name),
  last_name = VALUES(last_name),
  title = VALUES(title),
  headline = VALUES(headline),
  person_industry = VALUES(person_industry),
  image_url = VALUES(image_url),
  person_city = VALUES(person_city),
  person_state = VALUES(person_state),
  person_country_code = VALUES(person_country_code),
  person_country = VALUES(person_country),
  person_region = VALUES(person_region),
  org_uuid = VALUES(org_uuid),
  org_name = VALUES(org_name),
  org_website = VALUES(org_website),
  org_domain = VALUES(org_domain),
  org_linkedin_url = VALUES(org_linkedin_url),
  org_employees = VALUES(org_employees),
  org_industry = VALUES(org_industry),
  org_city = VALUES(org_city),
  org_state = VALUES(org_state),
  org_country_code = VALUES(org_country_code),
  org_country = VALUES(org_country),
  org_region = VALUES(org_region),
  emails_json = VALUES(emails_json),
  phones_json = VALUES(phones_json),
  raw_json = VALUES(raw_json)
""".strip()

    params = (
        int(search_id),
        (None if source_row_id is None else int(source_row_id)),
        str(linkedin_url),

        person_uuid, full_name, first_name, last_name,
        title, headline, person_industry, image_url,

        person_city, person_state, person_country_code, person_country, person_region,

        org_uuid, org_name, org_website, org_domain, org_linkedin_url, org_employees, org_industry,
        org_city, org_state, org_country_code, org_country, org_region,

        (None if emails is None else json.dumps(emails, ensure_ascii=False)),
        (None if phones is None else json.dumps(phones, ensure_ascii=False)),
        json.dumps(payload, ensure_ascii=False),
    )

    conn = await get_db_connection()
    async with conn.cursor() as cursor:
        await cursor.execute(sql_insert, params)
    conn.close()
