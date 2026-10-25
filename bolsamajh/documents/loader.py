"""Document loader — PDF, DOCX, and web page ingestion."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

log = logging.getLogger(__name__)


@dataclass
class DocumentPage:
    """A single page/section of a loaded document."""
    text: str
    page_number: int = 0        # 1-indexed (0 = unknown)
    section: str = ""           # Section heading if available
    source: str = ""            # File path or URL


@dataclass
class Document:
    """A loaded document with page-level content."""
    title: str
    source: str                  # File path or URL
    pages: list[DocumentPage] = field(default_factory=list)
    doc_type: str = ""           # "pdf", "docx", "web"

    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages if p.text.strip())

    @property
    def page_count(self) -> int:
        return len(self.pages)


def load_pdf(file_path: str) -> Document:
    """Load a PDF file using PyMuPDF."""
    import fitz  # PyMuPDF

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF not found: {file_path}")

    log.info("Loading PDF: %s", path.name)
    doc = fitz.open(str(path))

    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text")
        if text.strip():
            pages.append(DocumentPage(
                text=text.strip(),
                page_number=page_num + 1,
                source=str(path),
            ))

    title = doc.metadata.get("title", "") or path.stem
    doc.close()

    result = Document(
        title=title,
        source=str(path),
        pages=pages,
        doc_type="pdf",
    )
    log.info("Loaded PDF: %s (%d pages with text)", title, len(pages))
    return result


def load_docx(file_path: str) -> Document:
    """Load a Word document using python-docx."""
    from docx import Document as DocxDoc

    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"DOCX not found: {file_path}")

    log.info("Loading DOCX: %s", path.name)
    docx = DocxDoc(str(path))

    # Group paragraphs by sections (using headings)
    pages = []
    current_section = ""
    current_text_parts = []
    page_num = 1

    for para in docx.paragraphs:
        if para.style and para.style.name and para.style.name.startswith("Heading"):
            # Save previous section
            if current_text_parts:
                pages.append(DocumentPage(
                    text="\n".join(current_text_parts),
                    page_number=page_num,
                    section=current_section,
                    source=str(path),
                ))
                page_num += 1
                current_text_parts = []
            current_section = para.text.strip()

        if para.text.strip():
            current_text_parts.append(para.text.strip())

    # Save last section
    if current_text_parts:
        pages.append(DocumentPage(
            text="\n".join(current_text_parts),
            page_number=page_num,
            section=current_section,
            source=str(path),
        ))

    title = path.stem
    result = Document(
        title=title,
        source=str(path),
        pages=pages,
        doc_type="docx",
    )
    log.info("Loaded DOCX: %s (%d sections)", title, len(pages))
    return result


def load_webpage(url: str) -> Document:
    """Load a web page using trafilatura."""
    import trafilatura

    log.info("Loading web page: %s", url[:80])
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        raise ValueError(f"Could not fetch URL: {url}")

    text = trafilatura.extract(
        downloaded,
        include_comments=False,
        include_tables=True,
        include_links=False,
    )

    if not text:
        raise ValueError(f"Could not extract text from: {url}")

    # Split into paragraphs as "pages"
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    pages = []
    for i, para in enumerate(paragraphs, 1):
        pages.append(DocumentPage(
            text=para,
            page_number=i,
            section=f"Section {i}",
            source=url,
        ))

    title = url.split("/")[-1] or "Web Page"
    result = Document(
        title=title,
        source=url,
        pages=pages,
        doc_type="web",
    )
    log.info("Loaded web page: %d sections extracted", len(pages))
    return result


def load_text_file(path_str: str) -> Document:
    """Load plain text or markdown file."""
    path = Path(path_str)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path_str}")

    content = path.read_text(encoding="utf-8", errors="replace")
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [content.strip()] if content.strip() else ["(Empty document)"]

    pages = []
    for i, para in enumerate(paragraphs, 1):
        pages.append(DocumentPage(
            text=para,
            page_number=i,
            section=f"Section {i}",
            source=str(path),
        ))

    title = path.stem
    result = Document(
        title=title,
        source=str(path),
        pages=pages,
        doc_type=path.suffix.lstrip("."),
    )
    log.info("Loaded text file: %s (%d sections)", title, len(pages))
    return result


def load_document(source: str) -> Document:
    """Auto-detect and load a document from file path or URL."""
    source = source.strip()

    if source.startswith(("http://", "https://")):
        return load_webpage(source)

    path = Path(source)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return load_pdf(source)
    elif suffix in (".docx", ".doc"):
        return load_docx(source)
    elif suffix in (".txt", ".md", ".markdown", ".rst"):
        return load_text_file(source)
    else:
        raise ValueError(
            f"Unsupported document type: {suffix}. "
            "Supported: .pdf, .docx, .txt, .md, or a URL."
        )

