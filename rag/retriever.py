from rag.embedding import embed_texts


async def retrieve_context(store, query: str, k: int = 5) -> list[str]:
    if store is None:
        return []

    query_vector = embed_texts([query])[0]
    return store.similarity_search(query_vector, k=k)