from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from bs4 import BeautifulSoup
import httpx
from typing import List

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

SCRAPER_API_KEY = "a0e23f40c25092d8d5f76d85a667d11d"

class ScrapeRequest(BaseModel):
    url: str
    keywords: List[str]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/scrape")
async def scrape(req: ScrapeRequest):
    try:
        scraper_url = f"http://api.scraperapi.com?api_key={SCRAPER_API_KEY}&url={req.url}"

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.get(scraper_url)

        soup = BeautifulSoup(response.text, "html.parser")
        all_links = soup.find_all("a", href=True)

        base_url = req.url.rstrip("/")
        seen = set()
        matched = []

        for tag in all_links:
            href = tag["href"]
            text = tag.get_text(strip=True)

            if href.startswith("/"):
                href = base_url + href
            elif href.startswith("http"):
                pass
            else:
                continue

            if href in seen:
                continue
            seen.add(href)

            for kw in req.keywords:
                kw = kw.strip()
                if (kw.lower() in href.lower() or
                    kw.lower() in text.lower()):
                    matched.append({
                        "url": href,
                        "text": text if text else href
                    })
                    break

        return {
            "total_links": len(seen),
            "matched_links": len(matched),
            "links": matched
        }

    except Exception as e:
        return {
            "error": str(e),
            "links": [],
            "total_links": 0,
            "matched_links": 0
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
