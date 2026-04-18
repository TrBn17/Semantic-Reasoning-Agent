from semantic_reasoning_agent.llm.base import ProviderAdapter


class EchoAdapter(ProviderAdapter):
    provider = "echo"

    def generate_reply(self, prompt: str) -> str:
        return f"echo: {prompt}"
