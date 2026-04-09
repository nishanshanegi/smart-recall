import torch
from sentence_transformers import SentenceTransformer
from app.services.llm_base import get_llm

class AIService:
    def __init__(self):
        torch.set_num_threads(1)
        # 1. THE SEARCH BRAIN (Local)
        # Load the model once into memory
        print("📥 Loading Local Embedding Model...")
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
        print("✅ Embedding Model Loaded!")

        # 2. THE ANSWERING BRAIN (Generic LLM)
        # Use the factory to get our configured LLM (Groq/OpenAI)
        print("🔌 Connecting to LLM Service...")
        self.llm = get_llm()
        print("✅ LLM Connected!")

    def get_embedding(self, text: str):
        # Turns text into math for semantic search
        embedding = self.embed_model.encode(text)
        return embedding.tolist()

    def generate_answer(self, question: str, context: str):
        # WHAT: We pass the heavy lifting to our LLM provider
        # WHY: This prevents the 'AttributeError' by using the correct object
        return self.llm.generate_answer(question, context)

# Create a single instance to be used everywhere
ai_service = AIService()