import re
from datetime import datetime 
# Imports dateutil parser to convert messy date strings into actual date objects.
from dateutil import parser as date_parser 

# Regular expressions for month patterns and date patterns
MONTH_PATTERN = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
NUMERIC_MONTH_PATTERN = r"\d{1,2}[\/\-]\d{4}"
DATE_PATTERN = rf"(?:{MONTH_PATTERN}\s+\d{{4}}|{NUMERIC_MONTH_PATTERN}|\d{{4}})"
DATASET_MAX_DATE = datetime(2018, 12, 31)

# Regular expression to find job headers in the text
JOB_HEADER_RE = re.compile(
    rf"(?m)(?:^|\n|•|\-|–)\s*(?P<title>[^\n]{{3,}}?)\s+"
    rf"(?P<start>{DATE_PATTERN})\s*(?:to|[-–—])\s*"
    rf"(?P<end>Present|Current|{DATE_PATTERN})",
    re.I,
)
VERB_CUES = {
    "accomplished",
    "administered",
    "analyzed",
    "built",
    "collaborated",
    "communicated",
    "configured",
    "coordinated",
    "created",
    "delivered",
    "designed",
    "developed",
    "implemented",
    "installed",
    "led",
    "managed",
    "migrated",
    "monitored",
    "oversaw",
    "planned",
    "prepared",
    "resolved",
    "reviewed",
    "supported",
    "tested",
    "troubleshot",
}


def parse_date(text, now=None):
    """
    Parses a date string into a YYYY-MM-DD format.
    Args:
        text: The date string to parse
        now: The current date
    Returns:
        The parsed date in YYYY-MM-DD format
    """
    if not text:
        return None
    token = text.strip()
    if token.lower() in {"present", "current", "now", "today", "till date", "ongoing"}:
        dt = DATASET_MAX_DATE
    else:
        try:
            dt = date_parser.parse(token, fuzzy=True)
        except Exception:
            return None
    if dt > DATASET_MAX_DATE:
        dt = DATASET_MAX_DATE
    return dt.strftime("%Y-%m-%d")


def clean_company_name(text):
    """
    Cleans a company name by removing unnecessary text and whitespace.
    Args:
        text: The company name to clean
    Returns:
        The cleaned company name
    """
    text = re.sub(r"Company Name\s*[:\-]?\s*", "", text or "", flags=re.I)
    text = re.sub(r"\s*City\s*,\s*State.*$", "", text)
    text = re.sub(r"\s*\|\s*.+$", "", text)
    text = re.sub(r"[^\w&,.\- ]", "", text)
    return text.strip(" ,.–|")


def _sanitize_company(text):
    """
    Sanitizes a company name by removing unnecessary text and whitespace.
    Args:
        text: The company name to sanitize
    Returns:
        The sanitized company name
    """
    cleaned = clean_company_name(text)
    if not cleaned:
        return ""
    if len(cleaned) > 80 or len(cleaned.split()) > 10:
        return ""
    if not re.search(r"[A-Za-z]", cleaned):
        return ""
    return cleaned


def _split_title_and_company(text):
    """
    Splits a title and company name.
    Args:
        text: The text to split
    Returns:
        The split title and company name
    """
    title = (text or "").strip()
    company = ""
    if not title:
        return "", ""

    company_match = re.search(r"(Company\s+Name[^\n]*|Company\s+[A-Za-z].*|[A-Za-z0-9&.\- ]+ Company)", title, re.I)
    if company_match:
        company = _sanitize_company(company_match.group(0))
        title = title[:company_match.start()].strip(" ,.–|")
    elif title.lower().endswith(" city") or title.lower().endswith(" city , state"):
        parts = re.split(r"\s+City.*", title, flags=re.I)
        if len(parts) > 1:
            company = _sanitize_company(title[len(parts[0]):])
            title = parts[0].strip(" ,.–|")

    return title.strip(" ,.–|"), company.strip(" ,.–|")


def _normalize_work_text(work_text):
    """
    Normalizes the work text by replacing carriage returns with newlines and removing extra whitespace.
    Args:
        work_text: The work text to normalize
    Returns:
        The normalized work text
    """
    text = (work_text or "").replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n", text)
    text = re.sub(rf"(?<!\s)({MONTH_PATTERN}\s+\d{{4}})", r" \1", text, flags=re.I)
    text = re.sub(r"\u2022", "\n•", text)

    def merge_date_header(match):
        date_part = match.group("date").strip()
        title_part = match.group("title").strip()
        if not title_part:
            return match.group(0)
        prefix = match.group("prefix")
        return f"{prefix}{title_part} {date_part}\n"

    date_only_pattern = re.compile(
        rf"(?m)(?P<prefix>^|\n)(?P<date>{DATE_PATTERN}\s*(?:to|[-–—])\s*(?:Present|Current|{DATE_PATTERN}))\s*\n(?P<title>[A-Za-z][^\n]+)"
    )
    text = date_only_pattern.sub(merge_date_header, text)
    return text.strip()


def _extract_company_and_description(trailing_text):
    """
    Extracts a company name and description from the trailing text.
    Args:
        trailing_text: The trailing text to extract from
    Returns:
        The extracted company name and description
    """
    trailing_text = trailing_text.strip()
    if not trailing_text:
        return "", ""

    tokens = trailing_text.split()
    company_tokens = []
    desc_tokens = tokens

    for idx, raw_token in enumerate(tokens):
        token = re.sub(r"[^\w]", "", raw_token).lower()
        if token in VERB_CUES:
            company_tokens = tokens[:idx]
            desc_tokens = tokens[idx:]
            break
    else:
        period_idx = trailing_text.find(".")
        if period_idx != -1:
            company_tokens = trailing_text[:period_idx].split()
            desc_tokens = trailing_text[period_idx + 1 :].split()

    company = _sanitize_company(" ".join(company_tokens).strip(" ,.-"))
    if company:
        description = " ".join(desc_tokens).strip()
    else:
        description = trailing_text

    return company, description


def _line_based_jobs(work_text):
    """
    Extracts jobs from the work text.
    Args:
        work_text: The work text to extract jobs from
    Returns:
        The extracted jobs
    """
    lines = [l.strip() for l in (work_text or "").split("\n") if l.strip()]
    jobs = []
    current_job = None
    current_desc = []

    i = 0
    while i < len(lines):
        line = lines[i]

        date_match = re.search(r"(?:\d{4}|Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present|Current)", line, re.I)
        if date_match and len(line) > 15:
            dates = re.findall(r"(\w+\s+\d{4}|\d{4}|Present|Current)", line, re.I)
            if len(dates) >= 1:
                if current_job:
                    current_job["description"] = " ".join(current_desc).strip()
                    jobs.append(current_job)

                start_str = dates[0]
                end_str = dates[-1] if len(dates) > 1 else "Present"

                start_date = parse_date(start_str)
                end_date = parse_date(end_str)

                title = line.split(" at ")[0].split(" | ")[0]
                title = re.sub(r"\s*\d{4}.*$", "", title).strip()
                company = clean_company_name(line)
                title, embedded_company = _split_title_and_company(title)
                if embedded_company:
                    company = embedded_company or company
                company = _sanitize_company(company) or "Unknown Company"

                current_job = {
                    "company": company,
                    "title": title or "Unknown Role",
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration_years": 0.0,
                    "description": "",
                }
                current_desc = []
                i += 1
                continue

        if current_job:
            current_desc.append(line)
        i += 1

    if current_job:
        current_job["description"] = " ".join(current_desc).strip()
        jobs.append(current_job)

    jobs = _compute_job_durations(jobs)
    for job in jobs:
        title, embedded_company = _split_title_and_company(job["title"])
        if embedded_company and (not job["company"] or job["company"].lower() == "unknown company"):
            job["company"] = embedded_company
        job["title"] = title or job["title"]
        sanitized = _sanitize_company(job["company"])
        job["company"] = sanitized or "Unknown Company"
    return jobs


def _compute_job_durations(jobs):
    """
    Computes the duration of each job.
    Args:
        jobs: The jobs to compute the duration of
    Returns:
        The computed jobs
    """
    cleaned = []
    now = DATASET_MAX_DATE
    now_str = now.strftime("%Y-%m-%d")
    for job in jobs:
        if job.get("start_date") and job.get("end_date"):
            try:
                s = datetime.strptime(job["start_date"], "%Y-%m-%d")
                e = datetime.strptime(job["end_date"], "%Y-%m-%d") if job["end_date"] != now_str else now
                months = (e.year - s.year) * 12 + e.month - s.month
                job["duration_years"] = round(months / 12.0, 1)
                job["duration_months"] = months
            except Exception:
                job["duration_years"] = 0.0
                job["duration_months"] = 0
        else:
            job["duration_years"] = 0.0
            job["duration_months"] = 0
        if job.get("duration_months", 0) > 0:
            cleaned.append(job)

    return cleaned


def split_into_jobs(work_text):
    """
    Splits the work text into jobs.
    Args:
        work_text: The work text to split into jobs
    Returns:
        The split jobs
    """
    normalized = _normalize_work_text(work_text)
    if not normalized:
        return []

    jobs = []
    matches = list(JOB_HEADER_RE.finditer(normalized))

    if matches:
        for idx, match in enumerate(matches):
            end_span = match.end()
            next_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(normalized)

            raw_title = match.group("title").strip(" ,.-")
            raw_title = re.sub(r"^Experience\s+", "", raw_title, flags=re.I)
            title = raw_title or "Unknown Role"

            start_date = parse_date(match.group("start"))
            end_date = parse_date(match.group("end"))

            trailing = normalized[end_span:next_start]
            company, description = _extract_company_and_description(trailing)
            company = _sanitize_company(company) or "Unknown Company"

            jobs.append(
                {
                    "company": company or "Unknown Company",
                    "title": title,
                    "start_date": start_date,
                    "end_date": end_date,
                    "duration_years": 0.0,
                    "duration_months": 0,
                    "description": description,
                }
            )

        jobs = _compute_job_durations(jobs)
        for job in jobs:
            title, embedded_company = _split_title_and_company(job["title"])
            if embedded_company and (not job["company"] or job["company"].lower() == "unknown company"):
                job["company"] = embedded_company
            job["title"] = title or job["title"]
            sanitized = _sanitize_company(job["company"])
            job["company"] = sanitized or "Unknown Company"
        return jobs

    return _line_based_jobs(work_text)


def calculate_total_experience(jobs):
    """
    Calculates the total experience of the jobs.
    Args:
        jobs: The jobs to calculate the total experience of
    Returns:
        The total experience
    """
    total_months = 0
    periods = []
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d")

    for job in jobs:
        start = job.get("start_date")
        end = job.get("end_date") or now_str
        if not start:
            continue
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d") if end != now_str else now
            if start_dt >= end_dt:
                continue
            months = (end_dt.year - start_dt.year) * 12 + end_dt.month - start_dt.month
            if months <= 0:
                continue
            if any(max(start_dt, ps) < min(end_dt, pe) for ps, pe in periods):
                continue
            periods.append((start_dt, end_dt))
            total_months += months
        except Exception:
            continue

    return round(total_months / 12.0, 1)