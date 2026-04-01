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
        # This is where the 'client' actually lives!
        self.client = openai.OpenAI(api_key=api_key, base_url=base_url)
        self.model = model_name

    def generate_answer(self, question: str, context: str) -> str:
        # WHAT: The Strict Persona Prompt
        # WHY: To force the AI to be concise and stop using "filler" phrases.
        prompt = f"""
        You are an elite Personal Intelligence Assistant. 
        Your goal is to provide direct, factual answers based EXCLUSIVELY on the provided context.

        RULES:
        1. Be concise and authoritative. 
        2. DO NOT use phrases like "Based on the context," "It seems," or "I assume."
        3. Just provide the answer. If there are multiple pieces of info, list them clearly.
        4. If the answer is not in the context, say: "No relevant information found in your vault."

        CONTEXT:
        {context}

        USER QUESTION:
        {question}

        ANSWER:
        """
        
        # We use 'self.client' here because it belongs to this class
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1 # Low temperature = factual and precise
        )
        return response.choices[0].message.content

# 3. THE FACTORY
def get_llm():
    # If we have Groq, use it.
    if settings.GROQ_API_KEY:
        return OpenAILikeLLM(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1",
            model_name="llama-3.1-8b-instant"
        )
    # Fallback for OpenAI (optional)
    elif hasattr(settings, 'OPENAI_API_KEY') and settings.OPENAI_API_KEY:
        return OpenAILikeLLM(
            api_key=settings.OPENAI_API_KEY,
            base_url="https://api.openai.com/v1",
            model_name="gpt-4o-mini"
        )
    else:
        raise Exception("No LLM API Key found! Check your .env")