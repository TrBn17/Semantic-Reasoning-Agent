from semantic_reasoning_agent.llm.base import ProviderAdapter


class EchoAdapter(ProviderAdapter):
    provider = "echo"

    def generate_reply(self, prompt: str, *, system_prompt: str | None = None) -> str:
        if system_prompt:
            return f"echo[{system_prompt}]: {prompt}"
        return f"echo: {prompt}"
