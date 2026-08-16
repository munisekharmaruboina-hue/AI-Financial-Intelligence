from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_articles(articles: list[dict], chunk_size: int = 500, chunk_overlap: int = 50) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    chunks = []
    for article in articles:
        text = article.get("content") or article.get("summary", "")
        if not text:
            continue
        title = article.get("title", "")
        full_text = f"{title}\n{text}" if title else text
        chunks.extend(splitter.split_text(full_text))

    return chunks