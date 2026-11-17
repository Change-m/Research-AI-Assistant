from mcp.server.fastmcp import FastMCP
import httpx
import urllib.parse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

# Initialize the FastMCP server
mcp = FastMCP("ResearchAssistantServer")

@mcp.tool()
async def search_arxiv(query: str, max_results: int = 3) -> List[Dict[str, Any]]:
    encoded_query = urllib.parse.quote(query)
    url = f"http://export.arxiv.org/api/query?search_query=all:{encoded_query}&max_results={max_results}&sortBy=relevance&sortOrder=descending"

    x_client = httpx.AsyncClient()
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=15.0)
            if response.status_code != 200:
                return [{"error": f"Failed to fetch data from arXiv API. Status code: {response.status_code}"}]

            # Parse Atom XML feed returned by arXiv
            root = ET.fromstring(response.text)

            # arXiv API uses Atom namespace
            namespace = {'atom': 'http://www.w3.org/2005/Atom'}
            papers = []

            for entry in root.findall('atom:entry', namespace):
                title = entry.find('atom:title', namespace)
                summary = entry.find('atom:summary', namespace)
                published = entry.find('published', namespace)
                id_elem = entry.find('atom:id', namespace)

                # Extra authors
                authors = [
                    author.find('atom:name', namespace).text
                    for author in entry.findall('atom:author', namespace)
                    if author.find('atom:name', namespace) is not None
                ]

                # Extract PDF link specifically
                pdf_link = ""
                for link in entry.findall('atom:link', namespace):
                    if link.attrib.get('title') == 'pdf' or link.attrib.get('type') == 'application/pdf':
                        pdf_link = link.attrib.get('href', '')

                paper = {
                    "id": id_elem.text.split('/')[-1] if id_elem is not None else " ",
                    "title": title.text.strip().replace('\n', ' ') if title is not None else "No Title",
                    "author": authors,
                    "summary": summary.text.strip().replace('\n', ' ') if summary is not None else "No Summary",
                    "published": published.text[:10] if published is not None else "",
                    "pdf_url": pdf_link or (id_elem.text.replace('abs', 'pdf') + '.pdf' if id_elem is not None else "")
                }
                papers.append(paper)

            return papers if papers else [{"message": "No matching papers found."}]

        except Exception as e:
            return [{"error": f"An error occurred while querying arXiv: {str(e)}"}]

if __name__=="__main__":
    mcp.run()