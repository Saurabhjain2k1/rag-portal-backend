# app/services/url_loader.py

import requests
from bs4 import BeautifulSoup
from langchain_core.documents import Document  # from langchain >=0.1


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def load_url_with_bs4(url: str) -> list[Document]:
    """
    Fetch HTML using requests with browser-like headers,
    parse with BeautifulSoup, strip scripts/styles/nav etc,
    and return a single LangChain Document.

    This avoids BSHTMLLoader + Windows encoding issues.
    """
    try:
        resp = requests.get(url, timeout=20, headers=HEADERS)
        resp.raise_for_status()

        # Let requests figure out encoding; fallback to utf-8
        if not resp.encoding:
            resp.encoding = "utf-8"

        html = resp.text

        soup = BeautifulSoup(html, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
            tag.decompose()

        # Get visible text
        text = soup.get_text(separator="\n", strip=True)

        if not text.strip():
            raise RuntimeError("No extractable text from URL")

        doc = Document(
            page_content=text,
            metadata={"source": url},
        )
        return [doc]

    except Exception as e:
        raise RuntimeError(f"Failed to fetch or parse URL: {str(e)}")
