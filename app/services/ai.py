from sentence_transformers import SentenceTransformer
from app.services.llm_base import get_llm # <--- Import our new factory

class AIService:
    def __init__(self):
        # 1. THE SEARCH BRAIN (Local)
        # WHAT: Load the model ONCE.
        print("📥 Loading Local Embedding Model...")
        self.embed_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("✅ Embedding Model Loaded!")

        # 2. THE ANSWERING BRAIN (Generic LLM)
        # WHAT: Use the factory to get our configured LLM (Groq/OpenAI)
        print("🔌 Connecting to LLM Service...")
        self.llm = get_llm()
        print("✅ LLM Connected!")

    def get_embedding(self, text: str):
        # Turns text into math for searching
        embedding = self.embed_model.encode(text)
        return embedding.tolist()

    def generate_answer(self, question: str, context: str):
        # WHAT: This is the "RAG" step. 
        # WHY: We just tell our 'llm' object to do its job. 
        # We don't care if it's Groq or OpenAI inside.
        return self.llm.generate_answer(question, context)

# Create a single instance to be used everywhere
ai_service = AIService()