import openai
from abc import ABC, abstractmethod
from app.core.config import settings

# 1. THE CONTRACT
class BaseLLM(ABC):
    @abstractmethod
    def generate_answer(self, question: str, context: str) -> str:
        pass

# 2. THE IMPLEMENTATION (OpenAI-Compatible)
class OpenAILikeLLM(BaseLLM):
    def __init__(self, api_key: str, base_url: str, model_name: str):
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model_name

    def generate_answer(self, question: str, context: str) -> str:
        prompt = f"Context: {context}\n\nQuestion: {question}"
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content

# 3. THE FACTORY
def get_llm():
    # If we have Groq, use it. Otherwise, use OpenAI or raise error.
    if settings.GROQ_API_KEY:
        return OpenAILikeLLM(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model_name="llama-3.1-8b-instant"
        )
    # You can add elif for OpenAI here later!
    else:
        raise Exception("No LLM API Key found! Check your .env")