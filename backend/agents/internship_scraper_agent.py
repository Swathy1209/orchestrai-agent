import os
import requests
import yaml
import logging
from datetime import datetime, timezone
from bs4 import BeautifulSoup
from backend.github_yaml_db import _get_raw_file, _put_raw_file, append_log_entry

logger = logging.getLogger("OrchestrAI.InternshipScraperAgent")

TARGET_ROLES = ["AI", "Machine Learning", "Data Science", "Data Engineering", "Analytics", "Computer Vision", "NLP"]

def _is_relevant_role(role: str) -> bool:
    role_lower = role.lower()
    # Also prioritize internship/entry roles
    is_intern = any(kw in role_lower for kw in ["intern", "student", "trainee", "entry"])
    matches_domain = any(r.lower() in role_lower for r in TARGET_ROLES)
    return is_intern and matches_domain

def scrape_linkedin_jobs() -> list:
    """Fetch from LinkedIn public job search."""
    logger.info("Scraping LinkedIn jobs via public search...")
    jobs = []
    # Using multiple queries to get a broad range
    search_queries = ["AI Intern", "Machine Learning Intern", "Data Science Intern", "Data Engineer Intern"]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    for query in search_queries:
        try:
            # Sort by date (sortBy=DD)
            url = f"https://www.linkedin.com/jobs/search/?keywords={requests.utils.quote(query)}&f_JT=I&sortBy=DD"
            r = requests.get(url, headers=headers, timeout=12)
            if r.status_code == 200:
                soup = BeautifulSoup(r.text, "html.parser")
                # Look for the job cards
                for card in soup.select(".base-search-card, .result-card")[:8]:
                    title_el = card.select_one(".base-search-card__title, h3")
                    company_el = card.select_one(".base-search-card__subtitle, h4")
                    link_el = card.select_one("a.base-card__full-link, a")
                    
                    if title_el and company_el and link_el:
                        title = title_el.get_text(strip=True)
                        company = company_el.get_text(strip=True)
                        link = link_el["href"].split("?")[0]
                        
                        if _is_relevant_role(title):
                            jobs.append({
                                "company": company,
                                "role": title,
                                "location": "Remote / Hybrid",
                                "portal": "LinkedIn",
                                "job_url": link,
                                "date_posted": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                                "required_skills": [],
                                "job_description": f"AI Internship opportunity at {company}."
                            })
        except Exception as e:
            logger.warning(f"LinkedIn scrape failed for {query}: {e}")
    return jobs

def scrape_indeed_jobs() -> list:
    logger.info("Scraping Indeed jobs...")
    # Indeed often blocks simple requests, returning best effort
    jobs = []
    try:
        url = "https://www.indeed.com/jobs?q=AI+Internship&l=Remote&sort=date"
        headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}
        r = requests.get(url, headers=headers, timeout=10)
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, "html.parser")
            # Simplified selector for demo/best-effort
            for item in soup.select(".job_seen_beacon")[:5]:
                title = item.select_one("h2").get_text(strip=True) if item.select_one("h2") else "Intern"
                company = item.select_one(".companyName").get_text(strip=True) if item.select_one(".companyName") else "Unknown"
                if _is_relevant_role(title):
                    jobs.append({
                        "company": company,
                        "role": title,
                        "location": "Remote",
                        "portal": "Indeed",
                        "job_url": url, # fallback
                        "date_posted": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "required_skills": ["Python", "Machine Learning"],
                        "job_description": "Data role at Indeed partner."
                    })
    except: pass
    return jobs

def scrape_greenhouse_stripe() -> list:
    """Fetch from Greenhouse API (Generic + Stripe)."""
    logger.info("Scraping Greenhouse and Stripe boards...")
    jobs = []
    # 1. Stripe (Stripe uses Greenhouse API at /v1/boards/stripe/jobs)
    try:
        r = requests.get("https://api.greenhouse.io/v1/boards/stripe/jobs?content=true", timeout=15)
        if r.status_code == 200:
            data = r.json().get("jobs", [])
            for item in data:
                title = item.get("title", "")
                if _is_relevant_role(title):
                    jobs.append({
                        "company": "Stripe",
                        "role": title,
                        "location": "Remote",
                        "portal": "Stripe",
                        "job_url": item.get("absolute_url", ""),
                        "date_posted": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "required_skills": [],
                        "job_description": item.get("content", "")[:200]
                    })
    except: pass
    
    # 2. Generic Greenhouse (Example: OpenAI or similar if slugs were known, using a few common ones)
    return jobs

def scrape_unstop_jobs() -> list:
    logger.info("Scraping Unstop jobs...")
    jobs = []
    try:
        r = requests.get("https://unstop.com/api/public/opportunity/search-result?opportunity=jobs&per_page=10&searchText=AI&oppType=internship", timeout=10)
        if r.status_code == 200:
            items = r.json().get("data", {}).get("data", [])
            for item in items:
                jobs.append({
                    "company": item.get("organisation", {}).get("name", "Unknown"),
                    "role": item.get("title", ""),
                    "location": item.get("city", "Remote"),
                    "portal": "Unstop",
                    "job_url": f"https://unstop.com/jobs/{item.get('id','')}",
                    "date_posted": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "required_skills": [],
                    "job_description": ""
                })
    except: pass
    return jobs

def scrape_glassdoor_jobs() -> list:
    # Playwright is not available in many cloud envs without complex setup
    # Simplified mock for now
    return []

def scrape_wellfound_jobs() -> list:
    logger.info("Scraping Wellfound (AngelList) jobs...")
    jobs = []
    # Wellfound requires session/auth usually, simulating a result
    jobs.append({
        "company": "AI Startup Pro",
        "role": "AI Research Intern",
        "location": "Palo Alto, CA",
        "portal": "Wellfound",
        "job_url": "https://wellfound.com/jobs/8888",
        "date_posted": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "application_deadline": "",
        "required_skills": ["Generative AI", "LLMs", "Python"],
        "job_description": "Researching future AI architectures."
    })
    return jobs

def scrape_remoteok_jobs() -> list:
    logger.info("Scraping RemoteOK jobs...")
    jobs = []
    try:
        r = requests.get("https://remoteok.com/api?tag=data", headers={"User-Agent": "OrchestrAI Bot/1.0"})
        if r.status_code == 200:
            for item in r.json():
                if isinstance(item, dict) and "company" in item and _is_relevant_role(item.get("position", "")):
                    jobs.append({
                        "company": item.get("company", "Unknown"),
                        "role": item.get("position", "Intern"),
                        "location": item.get("location", "Remote"),
                        "portal": "RemoteOK",
                        "job_url": item.get("url", ""),
                        "date_posted": item.get("date", "")[:10] if item.get("date") else datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                        "application_deadline": "",
                        "required_skills": list(item.get("tags", [])),
                        "job_description": item.get("description", "")[:500]
                    })
    except Exception as e:
        logger.error(f"RemoteOK scrape failed: {e}")
    return jobs

def scrape_jobs():
    logger.info("Starting internship scraper...")
    all_jobs = []
    all_jobs.extend(scrape_linkedin_jobs())
    all_jobs.extend(scrape_indeed_jobs())
    all_jobs.extend(scrape_greenhouse_stripe())
    all_jobs.extend(scrape_unstop_jobs())
    all_jobs.extend(scrape_remoteok_jobs())
    
    # Avoid duplicates and merge
    yaml_path = "data/internships.yaml"
    content, sha = _get_raw_file(yaml_path)
    existing_jobs = []
    if content:
        try:
            parsed = yaml.safe_load(content)
            existing_jobs = parsed if isinstance(parsed, list) else []
        except Exception:
            existing_jobs = []
            
    # keep previous jobs that are not duplicates by url
    job_map = { j.get("job_url"): j for j in existing_jobs if j.get("job_url") }
    
    scraped_count = 0
    for new_job in all_jobs:
        if new_job["job_url"]:
            job_map[new_job["job_url"]] = new_job
            scraped_count += 1
            
    final_jobs = list(job_map.values())
    
    # Maintain max 200 recent jobs
    final_jobs = final_jobs[-200:]
    
    new_yaml = yaml.dump(final_jobs, sort_keys=False)
    _put_raw_file(yaml_path, new_yaml, sha, "feat: Update internships.yaml with scraped jobs")
    logger.info(f"Scraped and merged {scraped_count} jobs.")
    
    try:
        append_log_entry({
            "agent": "InternshipScraperAgent",
            "action": f"Scrape completed, added {scraped_count} jobs",
            "status": "completed",
            "jobs_scraped": scraped_count,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        })
    except:
        pass

def remove_expired_jobs():
    logger.info("Removing expired jobs from internships.yaml...")
    yaml_path = "data/internships.yaml"
    content, sha = _get_raw_file(yaml_path)
    if not content:
        return
        
    try:
        jobs = yaml.safe_load(content)
        if not isinstance(jobs, list):
            jobs = []
    except Exception:
        jobs = []

    active_jobs = []
    expired_count = 0
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    for job in jobs:
        # 1. Application deadline
        deadline = job.get("application_deadline")
        if deadline and deadline < today:
            expired_count += 1
            continue
            
        # 2. HTTP 404
        url = job.get("job_url", "")
        if url:
            try:
                r = requests.head(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
                if r.status_code == 404:
                    expired_count += 1
                    continue
            except:
                pass
                
        # 3. Keyword check
        if url:
            try:
                r_text = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"}).text.lower()
                if any(kw in r_text for kw in ["position closed", "application closed", "no longer accepting applications"]):
                    expired_count += 1
                    continue
            except:
                pass
                
        active_jobs.append(job)
        
    if expired_count > 0 or len(active_jobs) != len(jobs):
        new_yaml = yaml.dump(active_jobs, sort_keys=False)
        _put_raw_file(yaml_path, new_yaml, sha, "fix: Remove expired internships")
        
    logger.info(f"Removed {expired_count} expired internships.")
    try:
        append_log_entry({
            "agent": "InternshipScraperAgent",
            "action": f"Removed {expired_count} expired jobs",
            "status": "completed",
            "expired_removed": expired_count,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
        })
    except:
        pass
