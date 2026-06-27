import json
import os
from typing import List

from backend.database.chroma_client import ChromaClientManager
from backend.rag.embeddings import EmbeddingGenerator
from backend.schemas.rag import RAGQueryRequest, RAGQueryResponse, RetrievedDocument
from backend.utils.custom_logger import setup_logger

logger = setup_logger("rag.service")


class RAGService:
    """Service to handle Retrieval-Augmented Generation (RAG).

    Generates embeddings for user prompts, retrieves context from ChromaDB collections
    (pages, components, styles), compiles a context-rich prompt, and executes LLM queries
    (Gemini, OpenAI, or Anthropic) with a local mock fallback.
    """

    def __init__(self) -> None:
        self.chroma = ChromaClientManager()
        self.generator = EmbeddingGenerator()

    def query(self, request: RAGQueryRequest) -> RAGQueryResponse:
        logger.info(f"Executing RAG query for prompt: '{request.prompt}'...")

        # 1. Compute query vector
        query_vector = self.generator.get_embedding(request.prompt)

        # 2. Retrieve top-K relevant documents from ChromaDB
        retrieved_docs: List[RetrievedDocument] = []

        if request.collection_name:
            # Query specific collection
            logger.info(f"RAG: Querying specific collection '{request.collection_name}'...")
            query_res = self.chroma.query_similarity(
                collection_name=request.collection_name,
                query_vector=query_vector,
                limit=request.limit
            )
            for item in query_res.results:
                retrieved_docs.append(
                    RetrievedDocument(
                        id=item.id,
                        collection=request.collection_name,
                        document=item.document or "",
                        distance=item.distance,
                        metadata=item.metadata
                    )
                )
        else:
            # Query all three standard collections (pages, components, styles) and consolidate
            logger.info("RAG: Querying all collections (pages, components, styles)...")
            collections = ["pages", "components", "styles"]
            all_items = []
            
            for col in collections:
                try:
                    query_res = self.chroma.query_similarity(
                        collection_name=col,
                        query_vector=query_vector,
                        limit=request.limit
                    )
                    for item in query_res.results:
                        all_items.append(
                            RetrievedDocument(
                                id=item.id,
                                collection=col,
                                document=item.document or "",
                                distance=item.distance,
                                metadata=item.metadata
                            )
                        )
                except Exception as e:
                    logger.warning(f"Failed to query ChromaDB collection '{col}': {e}. Skipping collection.")

            # Sort consolidated results by distance ascending (closest first)
            all_items.sort(key=lambda x: x.distance)
            
            # Slice top-K results
            retrieved_docs = all_items[:request.limit]

        logger.info(f"RAG: Successfully retrieved {len(retrieved_docs)} context documents.")

        # 3. Detect configured API keys
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")

        # Skip placeholder keys
        if gemini_key == "your_gemini_api_key_here":
            gemini_key = None
        if openai_key == "your_openai_api_key_here":
            openai_key = None
        if anthropic_key == "your_anthropic_api_key_here":
            anthropic_key = None

        # Build combined prompt
        compiled_prompt = self._build_prompt(request.prompt, retrieved_docs)

        # 4. Invoke LLM provider or fallback
        if gemini_key:
            logger.info("Using Google Gemini provider for RAG query...")
            return self._call_gemini(compiled_prompt, retrieved_docs, request.prompt, gemini_key)
        elif openai_key:
            logger.info("Using OpenAI GPT provider for RAG query...")
            return self._call_openai(compiled_prompt, retrieved_docs, request.prompt, openai_key)
        elif anthropic_key:
            logger.info("Using Anthropic Claude provider for RAG query...")
            return self._call_anthropic(compiled_prompt, retrieved_docs, request.prompt, anthropic_key)
        else:
            logger.warning("No LLM API keys configured. Falling back to Mock RAG generator.")
            return self._run_mock_rag(request.prompt, retrieved_docs)

    def _build_prompt(self, user_prompt: str, retrieved_docs: List[RetrievedDocument]) -> str:
        """Assembles a synthesis prompt formatting retrieved layout artifacts as context."""
        context_parts = []
        for idx, doc in enumerate(retrieved_docs):
            context_parts.append(
                f"Context Element {idx + 1} (Collection: {doc.collection}, ID: {doc.id}, Distance: {doc.distance:.4f}):\n"
                f"Content/Code:\n{doc.document}\n"
                f"Metadata: {json.dumps(doc.metadata)}\n"
                f"----------------------------------------"
            )
        context_str = "\n\n".join(context_parts)

        prompt = f"""You are a principal designer and frontend engineer for Helix UI.
The user has provided the following prompt:
"{user_prompt}"

To help you formulate a highly contextual, accurate, and styling-compliant response, we retrieved the following relevant pages, styles, or code component elements from our vector database:

--- RETRIEVED CONTEXT ---
{context_str}
--- END OF CONTEXT ---

Instructions:
1. Synthesize the user request using the provided context blocks where relevant.
2. If they ask for UI components or code structure, refer to the components code and class naming conventions in the retrieved context.
3. Be highly technical, concise, and professional. Do not use emojis in your response.
4. Output your answer directly as plain text or Markdown.
"""
        return prompt

    def _call_gemini(
        self, prompt: str, retrieved: List[RetrievedDocument], original_prompt: str, api_key: str
    ) -> RAGQueryResponse:
        import google.generativeai as genai

        genai.configure(api_key=api_key)
        model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
        model = genai.GenerativeModel(model_name)
        try:
            response = model.generate_content(prompt)
            return RAGQueryResponse(
                prompt=original_prompt,
                answer=response.text,
                retrieved_contexts=retrieved,
                metadata={"provider": "gemini", "model": model_name}
            )
        except Exception as e:
            logger.error(f"Gemini RAG query failed: {e}")
            raise

    def _call_openai(
        self, prompt: str, retrieved: List[RetrievedDocument], original_prompt: str, api_key: str
    ) -> RAGQueryResponse:
        from openai import OpenAI

        base_url = os.getenv("OPENAI_API_BASE")
        model = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
        client = OpenAI(api_key=api_key, base_url=base_url)
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful RAG developer assistant."},
                    {"role": "user", "content": prompt}
                ]
            )
            return RAGQueryResponse(
                prompt=original_prompt,
                answer=response.choices[0].message.content,
                retrieved_contexts=retrieved,
                metadata={"provider": "openai", "model": model}
            )
        except Exception as e:
            logger.error(f"OpenAI RAG query failed: {e}")
            raise

    def _call_anthropic(
        self, prompt: str, retrieved: List[RetrievedDocument], original_prompt: str, api_key: str
    ) -> RAGQueryResponse:
        from anthropic import Anthropic

        client = Anthropic(api_key=api_key)
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            return RAGQueryResponse(
                prompt=original_prompt,
                answer="".join([block.text for block in message.content]),
                retrieved_contexts=retrieved,
                metadata={"provider": "anthropic", "model": "claude-3-5-sonnet-20240620"}
            )
        except Exception as e:
            logger.error(f"Anthropic RAG query failed: {e}")
            raise

    def _run_mock_rag(self, prompt: str, retrieved: List[RetrievedDocument]) -> RAGQueryResponse:
        """Dynamic mock answer generator utilizing the actual text fields of retrieved context documents."""
        logger.info("Executing mock RAG response generation...")

        if not retrieved:
            answer = "I searched the vector database but found no relevant layout elements or component codes."
        else:
            doc_refs = []
            for doc in retrieved:
                doc_refs.append(f"- Matched {doc.collection} ID '{doc.id}' with similarity distance {doc.distance:.4f}")
            
            doc_refs_str = "\n".join(doc_refs)
            
            # Extract sample code or content to make the mock answer realistic
            context_summary = ""
            for doc in retrieved[:2]:
                snippet = doc.document[:150].replace("\n", " ") + "..."
                context_summary += f"\nSnippet from {doc.collection} ({doc.id}): \"{snippet}\""

            answer = (
                f"This is a synthesized mock RAG response for prompt: \"{prompt}\"\n\n"
                f"Based on the semantic search, the following relevant items were retrieved:\n"
                f"{doc_refs_str}\n\n"
                f"Matched Context Summary:{context_summary}\n\n"
                f"Here is a layout synthesis recommendation:\n"
                f"- Retain structural consistency. Ensure styles match the colors from the retrieved styles.\n"
                f"- Align UI layouts using Tailwind classes matching the retrieved page structures.\n"
                f"- Re-use UI logic pattern from component code structures where appropriate."
            )

        return RAGQueryResponse(
            prompt=prompt,
            answer=answer,
            retrieved_contexts=retrieved,
            metadata={"provider": "mock", "fallback_active": True}
        )
