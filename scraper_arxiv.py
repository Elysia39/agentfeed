import requests
import html
import xml.etree.ElementTree as ET

def fetch_huggingface_daily_papers(limit=5):
    """
    Fetch trending AI papers from Hugging Face Daily Papers (100% zero-login).
    """
    url = "https://huggingface.co/api/daily_papers"
    headers = {
        "User-Agent": "AgentFeed/1.0 (Mozilla/5.0; AI Research Bot)"
    }
    results = []
    try:
        resp = requests.get(url, headers=headers, timeout=12)
        if resp.status_code == 200:
            data = resp.json()
            for item in data[:limit]:
                paper = item.get("paper", {})
                title = paper.get("title", "")
                paper_id = paper.get("id", "")
                summary = paper.get("summary", "")
                authors = [a.get("name") for a in paper.get("authors", [])[:3] if isinstance(a, dict)]
                upvotes = item.get("upvotes", 0)
                link = f"https://huggingface.co/papers/{paper_id}" if paper_id else ""
                arxiv_pdf = f"https://arxiv.org/pdf/{paper_id}.pdf" if paper_id else ""
                
                # Truncate summary
                short_sum = summary[:240] + ("..." if len(summary) > 240 else "") if summary else ""

                results.append({
                    "title": html.unescape(title),
                    "summary": html.unescape(short_sum),
                    "paper_id": paper_id,
                    "authors": ", ".join(authors) if authors else "AI Researchers",
                    "upvotes": upvotes,
                    "link": link,
                    "pdf_url": arxiv_pdf,
                    "source": "Hugging Face / ArXiv"
                })
    except Exception as e:
        print(f"⚠️ Failed to fetch HuggingFace daily papers: {e}")
    return results

def fetch_arxiv_category_papers(category="cs.AI", limit=5):
    """
    Fetch latest papers from Cornell ArXiv API.
    """
    url = f"http://export.arxiv.org/api/query?search_query=cat:{category}&sortBy=submittedDate&sortOrder=descending&max_results={limit}"
    results = []
    try:
        resp = requests.get(url, timeout=12)
        if resp.status_code == 200:
            root = ET.fromstring(resp.content)
            atom_ns = {"atom": "http://www.w3.org/2005/Atom"}
            for entry in root.findall("atom:entry", atom_ns):
                title_elem = entry.find("atom:title", atom_ns)
                title = title_elem.text.strip().replace("\n", " ") if title_elem is not None else ""
                summary_elem = entry.find("atom:summary", atom_ns)
                summary = summary_elem.text.strip().replace("\n", " ") if summary_elem is not None else ""
                id_elem = entry.find("atom:id", atom_ns)
                link = id_elem.text.strip() if id_elem is not None else ""
                published_elem = entry.find("atom:published", atom_ns)
                published = published_elem.text[:10] if published_elem is not None else ""
                
                short_sum = summary[:240] + ("..." if len(summary) > 240 else "")

                results.append({
                    "title": html.unescape(title),
                    "summary": html.unescape(short_sum),
                    "link": link,
                    "date": published,
                    "category": category,
                    "source": f"ArXiv ({category})"
                })
    except Exception as e:
        print(f"⚠️ Failed to fetch ArXiv {category}: {e}")
    return results

def fetch_all_arxiv_papers(arxiv_config):
    """
    Fetch papers for all configured ArXiv categories / HuggingFace.
    """
    # Always include top trending papers from Hugging Face
    all_papers = fetch_huggingface_daily_papers(limit=5)
    
    for item in arxiv_config:
        if not item.get("enabled", True):
            continue
        cat = item.get("category", "cs.AI")
        papers = fetch_arxiv_category_papers(category=cat, limit=item.get("limit", 3))
        all_papers.extend(papers)
    return all_papers

def fetch_single_arxiv_preview(category="cs.AI"):
    if category.lower() in ["hf", "trending", "huggingface"]:
        papers = fetch_huggingface_daily_papers(limit=4)
    else:
        papers = fetch_arxiv_category_papers(category, limit=4)
    return {
        "success": len(papers) > 0,
        "category": category,
        "papers": papers,
        "error": f"未能拉取到 ArXiv [{category}] 论文" if not papers else None
    }

if __name__ == "__main__":
    hf = fetch_huggingface_daily_papers(3)
    print(f"Fetched {len(hf)} trending papers from HuggingFace:")
    for p in hf:
        print(f"- [{p['upvotes']} 🌟] {p['title']} ({p['link']})")
