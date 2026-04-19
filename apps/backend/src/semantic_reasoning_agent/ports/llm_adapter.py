from abc import ABC, abstractmethod


class ProviderAdapter(ABC):
    provider: str

    @abstractmethod
    def generate_reply(self, prompt: str, *, system_prompt: str | None = None) -> str:
        """Return a single assistant reply for a user prompt."""
