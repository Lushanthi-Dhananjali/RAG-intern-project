import os
from typing import List, Union
from dotenv import load_dotenv

# OpenAI Embeddings
from openai import OpenAI

# Local Open-Source Embeddings (Fallback / Offline option)
from sentence_transformers import SentenceTransformer

load_dotenv()


class EmbeddingPipeline:
    """
    Unified embedding generator supporting both OpenAI (text-embedding-3-small)
    and local open-source models (BAAI/bge-large-en-v1.5).
    """

    def __init__(self, provider: str = "openai", local_model_name: str = "BAAI/bge-large-en-v1.5"):
        """
        :param provider: 'openai' or 'local'
        :param local_model_name: HuggingFace model name if using local embeddings
        """
        self.provider = provider.lower()

        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY is missing from environment variables.")
            self.client = OpenAI(api_key=api_key)
            self.openai_model = "text-embedding-3-small"
            print("🚀 Embedding Pipeline initialized with OpenAI (text-embedding-3-small)")

        elif self.provider == "local":
            print(f"⏳ Loading local embedding model '{local_model_name}' (this may take a moment)...")
            self.local_model = SentenceTransformer(local_model_name)
            print("✅ Local BGE Embedding Model loaded successfully!")

        else:
            raise ValueError("Invalid provider. Choose either 'openai' or 'local'.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings for a batch of text documents."""
        if not texts:
            return []

        if self.provider == "openai":
            response = self.client.embeddings.create(
                model=self.openai_model,
                input=texts
            )
            return [item.embedding for item in response.data]

        elif self.provider == "local":
            # Normalize embeddings to maintain cosine similarity metric quality
            embeddings = self.local_model.encode(texts, normalize_embeddings=True)
            return embeddings.tolist()

    def embed_query(self, text: str) -> List[float]:
        """Generates embedding for a single user query string."""
        if not text.strip():
            return []

        if self.provider == "openai":
            response = self.client.embeddings.create(
                model=self.openai_model,
                input=[text]
            )
            return response.data[0].embedding

        elif self.provider == "local":
            # For BGE models, prepending an instruction improves query performance
            instruction_text = f"Represent this sentence for searching relevant passages: {text}"
            embedding = self.local_model.encode([instruction_text], normalize_embeddings=True)
            return embedding[0].tolist()


# --- Demonstration Run ---
if __name__ == "__main__":
    sample_texts = [
        "Grade 8 Science: Photosynthesis chemical reaction equation.",
        "Grade 10 Mathematics: Solving quadratic equations using factoring."
    ]

    # Test with OpenAI
    try:
        pipeline = EmbeddingPipeline(provider="openai")
        embeddings = pipeline.embed_documents(sample_texts)
        print(f"\n✅ OpenAI Embeddings Generated! Count: {len(embeddings)}")
        print(f"   Vector Dimension Size: {len(embeddings[0])} dimensions")
    except Exception as e:
        print(f"\n⚠️ OpenAI embedding check skipped: {e}")

    # Test with Local BGE (Optional / Backup)
    # pipeline_local = EmbeddingPipeline(provider="local")
    # local_embeddings = pipeline_local.embed_documents(sample_texts)
    # print(f"✅ Local BGE Embeddings Generated! Vector Dimension: {len(local_embeddings[0])}")