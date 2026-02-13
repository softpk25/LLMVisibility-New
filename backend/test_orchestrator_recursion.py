import asyncio
import pytest
from typing import Dict, Any
from backend.services.llm_orchestrator import LLMOrchestrator, LLMProvider
from backend.core.exceptions import LLMProviderError

class FailingProvider(LLMProvider):
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        raise LLMProviderError("failing", "Always fails")
    
    async def analyze_image(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        raise LLMProviderError("failing", "Always fails")
    
    async def moderate_content(self, content: str, **kwargs) -> Dict[str, Any]:
        raise LLMProviderError("failing", "Always fails")

@pytest.mark.asyncio
async def test_orchestrator_prevents_recursion():
    orchestrator = LLMOrchestrator()
    # Replace all providers with failing ones
    orchestrator.providers = {
        "fail1": FailingProvider("key1"),
        "fail2": FailingProvider("key2")
    }
    
    payload = {"task_type": "text_generation", "prompt": "test"}
    
    # This should not raise RecursionError but LLMProviderError after trying both
    with pytest.raises(LLMProviderError) as excinfo:
        await orchestrator.generate(payload)
    
    assert "No LLM providers available or all attempted providers failed" in str(excinfo.value)
    print("\n✅ Orchestrator recursion test passed")

if __name__ == "__main__":
    asyncio.run(test_orchestrator_prevents_recursion())
