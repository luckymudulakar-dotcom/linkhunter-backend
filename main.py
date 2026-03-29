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

class ScrapeRequest(BaseModel):
    url: str
    keywords: List[str]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/scrape")
async def scrape(req: ScrapeRequest):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "max-age=0",
        }

        async with httpx.AsyncClient(
            timeout=30,
            follow_redirects=True,
            headers=headers
        ) as client:
            response = await client.get(req.url)

        soup = BeautifulSoup(response.text, "html.parser")
        all_links = soup.find_all("a", href=True)

        base_url = str(response.url).rstrip("/")
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
      
