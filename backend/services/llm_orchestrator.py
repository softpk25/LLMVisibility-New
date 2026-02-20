"""
LLM Orchestration Layer - Provider-agnostic abstraction
"""

import json
import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum

from core.config import settings
from core.logging_config import get_logger
from core.exceptions import LLMProviderError

logger = get_logger("llm_orchestrator")


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, api_key: str, model: str = None):
        self.api_key = api_key
        self.model = model
        self.provider_name = self.__class__.__name__.lower().replace('provider', '')
    
    @abstractmethod
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text content"""
        pass
    
    @abstractmethod
    async def analyze_image(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Analyze image content"""
        pass
    
    @abstractmethod
    async def moderate_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """Moderate content for safety"""
        pass
    
    async def generate(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Main generation method - routes to appropriate sub-method"""
        try:
            task_type = payload.get('task_type', 'text_generation')
            
            if task_type == 'text_generation':
                return await self.generate_text(
                    prompt=payload.get('prompt', ''),
                    **payload.get('parameters', {})
                )
            elif task_type == 'image_analysis':
                return await self.analyze_image(
                    image_path=payload.get('image_path', ''),
                    prompt=payload.get('prompt', ''),
                    **payload.get('parameters', {})
                )
            elif task_type == 'content_moderation':
                return await self.moderate_content(
                    content=payload.get('content', ''),
                    **payload.get('parameters', {})
                )
            else:
                raise LLMProviderError(
                    self.provider_name,
                    f"Unsupported task type: {task_type}"
                )
                
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            raise LLMProviderError(self.provider_name, str(e))


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation"""
    
    def __init__(self, api_key: str, model: str = "gpt-4"):
        super().__init__(api_key, model)
        # Import here to avoid dependency issues if not installed
        try:
            import openai
            self.client = openai.AsyncOpenAI(api_key=api_key)
        except ImportError:
            raise LLMProviderError("openai", "OpenAI package not installed")
    
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using OpenAI"""
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get('model', self.model),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=kwargs.get('max_tokens', settings.MAX_TOKENS),
                temperature=kwargs.get('temperature', settings.TEMPERATURE),
                **{k: v for k, v in kwargs.items() if k not in ['model', 'max_tokens', 'temperature']}
            )
            
            return {
                "success": True,
                "content": response.choices[0].message.content,
                "usage": response.usage.dict() if response.usage else {},
                "model": response.model,
                "provider": "openai"
            }
            
        except Exception as e:
            raise LLMProviderError("openai", f"Text generation failed: {str(e)}")
    
    async def analyze_image(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Analyze image using OpenAI Vision"""
        try:
            import base64
            
            # Read and encode image
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = await self.client.chat.completions.create(
                model=kwargs.get('model', "gpt-4-vision-preview"),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                            }
                        ]
                    }
                ],
                max_tokens=kwargs.get('max_tokens', settings.MAX_TOKENS),
                **{k: v for k, v in kwargs.items() if k not in ['model', 'max_tokens']}
            )
            
            return {
                "success": True,
                "analysis": response.choices[0].message.content,
                "usage": response.usage.dict() if response.usage else {},
                "model": response.model,
                "provider": "openai"
            }
            
        except Exception as e:
            raise LLMProviderError("openai", f"Image analysis failed: {str(e)}")
    
    async def moderate_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """Moderate content using OpenAI"""
        try:
            response = await self.client.moderations.create(input=content)
            
            return {
                "success": True,
                "flagged": response.results[0].flagged,
                "categories": response.results[0].categories.dict(),
                "category_scores": response.results[0].category_scores.dict(),
                "provider": "openai"
            }
            
        except Exception as e:
            raise LLMProviderError("openai", f"Content moderation failed: {str(e)}")


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation"""
    
    def __init__(self, api_key: str, model: str = "claude-3-sonnet-20240229"):
        super().__init__(api_key, model)
        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=api_key)
        except ImportError:
            raise LLMProviderError("anthropic", "Anthropic package not installed")
    
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Generate text using Anthropic Claude"""
        try:
            response = await self.client.messages.create(
                model=kwargs.get('model', self.model),
                max_tokens=kwargs.get('max_tokens', settings.MAX_TOKENS),
                temperature=kwargs.get('temperature', settings.TEMPERATURE),
                messages=[{"role": "user", "content": prompt}]
            )
            
            return {
                "success": True,
                "content": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "model": response.model,
                "provider": "anthropic"
            }
            
        except Exception as e:
            raise LLMProviderError("anthropic", f"Text generation failed: {str(e)}")
    
    async def analyze_image(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Analyze image using Anthropic Claude Vision"""
        try:
            import base64
            
            with open(image_path, "rb") as image_file:
                base64_image = base64.b64encode(image_file.read()).decode('utf-8')
            
            response = await self.client.messages.create(
                model=kwargs.get('model', "claude-3-sonnet-20240229"),
                max_tokens=kwargs.get('max_tokens', settings.MAX_TOKENS),
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image
                                }
                            }
                        ]
                    }
                ]
            )
            
            return {
                "success": True,
                "analysis": response.content[0].text,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                "model": response.model,
                "provider": "anthropic"
            }
            
        except Exception as e:
            raise LLMProviderError("anthropic", f"Image analysis failed: {str(e)}")
    
    async def moderate_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """Basic content moderation using Claude"""
        try:
            moderation_prompt = f"""
            Please analyze the following content for safety issues including:
            - Hate speech or discrimination
            - Violence or threats
            - Sexual content
            - Spam or misleading information
            - Profanity
            
            Content: {content}
            
            Respond with JSON format:
            {{
                "flagged": boolean,
                "categories": {{"hate": boolean, "violence": boolean, "sexual": boolean, "spam": boolean, "profanity": boolean}},
                "explanation": "brief explanation"
            }}
            """
            
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": moderation_prompt}]
            )
            
            try:
                result = json.loads(response.content[0].text)
            except json.JSONDecodeError:
                result = {"flagged": False, "categories": {}, "explanation": "Parse error"}
            
            return {
                "success": True,
                "flagged": result.get("flagged", False),
                "categories": result.get("categories", {}),
                "explanation": result.get("explanation", ""),
                "provider": "anthropic"
            }
            
        except Exception as e:
            raise LLMProviderError("anthropic", f"Content moderation failed: {str(e)}")


class MockLLMProvider(LLMProvider):
    """Mock provider for testing"""
    
    def __init__(self, api_key: str = "mock", model: str = "mock-model"):
        super().__init__(api_key, model)
    
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock text generation"""
        await asyncio.sleep(0.1)  # Simulate API delay
        
        return {
            "success": True,
            "content": f"Mock response for prompt: {prompt[:50]}...",
            "usage": {"input_tokens": 100, "output_tokens": 50},
            "model": self.model,
            "provider": "mock"
        }
    
    async def analyze_image(self, image_path: str, prompt: str, **kwargs) -> Dict[str, Any]:
        """Mock image analysis"""
        await asyncio.sleep(0.2)
        
        return {
            "success": True,
            "analysis": f"Mock image analysis for {image_path}: This appears to be a professional image with good composition.",
            "usage": {"input_tokens": 150, "output_tokens": 75},
            "model": self.model,
            "provider": "mock"
        }
    
    async def moderate_content(self, content: str, **kwargs) -> Dict[str, Any]:
        """Mock content moderation"""
        await asyncio.sleep(0.05)
        
        return {
            "success": True,
            "flagged": False,
            "categories": {"hate": False, "violence": False, "sexual": False},
            "provider": "mock"
        }


class LLMOrchestrator:
    """Main orchestrator for LLM operations"""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available LLM providers"""
        
        # OpenAI
        if settings.OPENAI_API_KEY:
            try:
                self.providers["openai"] = OpenAIProvider(settings.OPENAI_API_KEY)
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI provider: {e}")
        
        # Anthropic
        if settings.ANTHROPIC_API_KEY:
            try:
                self.providers["anthropic"] = AnthropicProvider(settings.ANTHROPIC_API_KEY)
                logger.info("Anthropic provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic provider: {e}")
        
        # Always add mock provider for testing
        self.providers["mock"] = MockLLMProvider()
        logger.info("Mock provider initialized")
        
        if not self.providers:
            logger.warning("No LLM providers available")
    
    async def generate(self, payload: Dict[str, Any], provider: str = None, tried_providers: set = None) -> Dict[str, Any]:
        """Generate content using specified or default provider"""
        
        if tried_providers is None:
            tried_providers = set()
            
        # Determine provider
        if not provider:
            provider = settings.DEFAULT_LLM_PROVIDER
        
        if provider not in self.providers or provider in tried_providers:
            # Try fallback providers
            available_providers = [p for p in self.providers.keys() if p not in tried_providers]
            if available_providers:
                provider = available_providers[0]
                logger.warning(f"Requested provider not available or already tried, using {provider}")
            else:
                raise LLMProviderError("orchestrator", "No LLM providers available or all attempted providers failed")
        
        tried_providers.add(provider)
        
        # Add metadata to payload
        payload.setdefault("metadata", {}).update({
            "provider": provider,
            "timestamp": asyncio.get_event_loop().time(),
            "request_id": payload.get("request_id", "unknown")
        })
        
        try:
            logger.info(f"--- Attempting LLM generation with provider: {provider} ---")
            
            # Add timeout to the generation call (30 seconds)
            result = await asyncio.wait_for(
                self.providers[provider].generate(payload),
                timeout=30.0
            )
            
            logger.info(f"✅ LLM generation successful with provider: {provider}")
            
            # Add orchestrator metadata
            result["orchestrator_metadata"] = {
                "provider_used": provider,
                "available_providers": list(self.providers.keys()),
                "processing_time": asyncio.get_event_loop().time() - payload["metadata"]["timestamp"]
            }
            
            return result
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Provider {provider} timed out after 30s")
            # Try fallback if available
            fallback_providers = [p for p in self.providers.keys() if p not in tried_providers]
            if fallback_providers:
                logger.info(f"Trying fallback provider: {fallback_providers[0]}")
                return await self.generate(payload, fallback_providers[0], tried_providers)
            raise LLMProviderError("orchestrator", f"All providers failed or timed out. Last provider {provider} timed out.")
            
        except LLMProviderError as e:
            logger.error(f"❌ Provider {provider} failed: {e.message}")
            
            # Try fallback if available
            fallback_providers = [p for p in self.providers.keys() if p not in tried_providers]
            if fallback_providers:
                logger.info(f"Trying fallback provider: {fallback_providers[0]}")
                return await self.generate(payload, fallback_providers[0], tried_providers)
            
            raise e
        except Exception as e:
            logger.error(f"❌ Unexpected error with provider {provider}: {str(e)}")
            raise e
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers"""
        return list(self.providers.keys())
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers"""
        status = {}
        for name, provider in self.providers.items():
            status[name] = {
                "available": True,
                "model": provider.model,
                "provider_class": provider.__class__.__name__
            }
        return status


# Global orchestrator instance
orchestrator = LLMOrchestrator()