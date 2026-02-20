"""
OpenAI Service for AI Content Generation
Generates engaging captions, images, and content for social media posts
"""

import httpx
import base64
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from config import get_settings


class OpenAIService:
    """Service for generating AI content using OpenAI API"""
    
    def __init__(self):
        self.settings = get_settings()
        self.api_key = self.settings.OPENAI_API_KEY
        self.base_url = "https://api.openai.com/v1"
        # Directory to save generated images
        self.generated_images_dir = Path(__file__).parent.parent / "generated_images"
        self.generated_images_dir.mkdir(exist_ok=True)
    
    def generate_caption(
        self, 
        image_url: Optional[str] = None,
        topic: Optional[str] = None,
        tone: str = "engaging",
        max_length: int = 200
    ) -> Optional[str]:
        """
        Generate an engaging caption for a social media post.
        
        Args:
            image_url: URL of the image (optional, for image-based captions)
            topic: Topic or theme for the post
            tone: Tone of the caption (engaging, professional, casual, etc.)
            max_length: Maximum length of the caption
            
        Returns:
            Generated caption or None if error
        """
        if not self.api_key:
            print("OpenAI API key not configured")
            return None
        
        # Build the prompt
        prompt = f"Create an engaging {tone} social media caption"
        
        if topic:
            prompt += f" about {topic}"
        
        if image_url:
            prompt += f" for an image. Make it visually descriptive and engaging."
        
        prompt += f" Keep it under {max_length} characters. Include relevant emojis. Make it compelling and encourage engagement."
        
        messages = [
            {
                "role": "system",
                "content": "You are a social media expert who creates viral, engaging captions for Facebook posts. Always include relevant emojis and make content compelling."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "max_tokens": 300,
                        "temperature": 0.7
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    caption = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    return caption
                else:
                    print(f"OpenAI API error: {response.status_code} - {response.text}")
                    return None
                    
        except Exception as e:
            print(f"Error generating caption: {e}")
            return None
    
    def generate_hashtags(self, caption: str, count: int = 5) -> list:
        """
        Generate relevant hashtags based on the caption.
        
        Args:
            caption: The post caption
            count: Number of hashtags to generate
            
        Returns:
            List of hashtags
        """
        if not self.api_key:
            return []
        
        prompt = f"Generate {count} relevant, popular hashtags for this social media post. Return only the hashtags, one per line, without numbers or bullets:\n\n{caption}"
        
        messages = [
            {
                "role": "system",
                "content": "You are a social media expert. Generate relevant, trending hashtags."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            with httpx.Client(timeout=20.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "max_tokens": 100,
                        "temperature": 0.5
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    text = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    # Extract hashtags
                    hashtags = [line.strip() for line in text.split('\n') if line.strip() and line.strip().startswith('#')]
                    return hashtags[:count]
                else:
                    return []
                    
        except Exception as e:
            print(f"Error generating hashtags: {e}")
            return []
    
    def generate_image(
        self,
        prompt: str,
        size: str = "1024x1024",
        quality: str = "standard",
        style: str = "vivid"
    ) -> Optional[Dict[str, Any]]:
        """
        Generate an image using DALL-E 3.
        
        Args:
            prompt: Description of the image to generate
            size: Image size (1024x1024, 1792x1024, or 1024x1792)
            quality: Image quality (standard or hd)
            style: Image style (vivid or natural)
            
        Returns:
            Dictionary with image_url, local_path, and filename if successful
        """
        if not self.api_key:
            print("OpenAI API key not configured")
            return None
        
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(
                    f"{self.base_url}/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": size,
                        "quality": quality,
                        "style": style,
                        "response_format": "b64_json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    image_data = data.get("data", [{}])[0]
                    b64_image = image_data.get("b64_json")
                    revised_prompt = image_data.get("revised_prompt", prompt)
                    
                    if b64_image:
                        # Generate unique filename
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        unique_id = str(uuid.uuid4())[:8]
                        filename = f"generated_{timestamp}_{unique_id}.png"
                        filepath = self.generated_images_dir / filename
                        
                        # Save image locally
                        image_bytes = base64.b64decode(b64_image)
                        with open(filepath, "wb") as f:
                            f.write(image_bytes)
                        
                        return {
                            "filename": filename,
                            "local_path": str(filepath),
                            "revised_prompt": revised_prompt,
                            "b64_image": b64_image
                        }
                else:
                    error_data = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
                    print(f"DALL-E API error: {response.status_code} - {error_data}")
                    return None
                    
        except Exception as e:
            print(f"Error generating image: {e}")
            return None
    
    def generate_image_prompt(
        self,
        topic: str,
        style: str = "professional",
        additional_context: str = ""
    ) -> Optional[str]:
        """
        Generate an optimized DALL-E prompt based on the topic.
        
        Args:
            topic: The main subject/topic for the image
            style: Visual style (professional, artistic, minimalist, etc.)
            additional_context: Any additional context or requirements
            
        Returns:
            Optimized prompt for DALL-E
        """
        if not self.api_key:
            return None
        
        prompt = f"""Create a detailed DALL-E 3 image prompt for a social media post about: {topic}

Style: {style}
{f'Additional requirements: {additional_context}' if additional_context else ''}

The prompt should:
1. Be highly descriptive and detailed
2. Specify lighting, composition, and mood
3. Be optimized for social media engagement
4. Avoid any text or words in the image
5. Be safe for all audiences

Return ONLY the image prompt, nothing else."""

        messages = [
            {
                "role": "system",
                "content": "You are an expert at creating DALL-E prompts that generate stunning, engaging social media images. Your prompts are detailed, artistic, and optimized for visual impact."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
        
        try:
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "gpt-4o-mini",
                        "messages": messages,
                        "max_tokens": 500,
                        "temperature": 0.8
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    image_prompt = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                    return image_prompt
                else:
                    print(f"OpenAI API error: {response.status_code}")
                    return None
                    
        except Exception as e:
            print(f"Error generating image prompt: {e}")
            return None
    
    def generate_complete_post(
        self,
        topic: str,
        post_type: str = "image",
        tone: str = "engaging",
        style: str = "professional",
        generate_image: bool = True,
        image_count: int = 1
    ) -> Optional[Dict[str, Any]]:
        """
        Generate a complete social media post with caption, hashtags, and optionally image(s).
        
        Args:
            topic: The main topic/theme for the post
            post_type: Type of post (text, image, carousel)
            tone: Tone for the caption
            style: Visual style for image generation
            generate_image: Whether to generate image(s)
            image_count: Number of images (for carousel)
            
        Returns:
            Dictionary with all generated content
        """
        result = {
            "topic": topic,
            "post_type": post_type,
            "caption": None,
            "hashtags": [],
            "images": [],
            "full_text": None
        }
        
        # Generate caption
        caption = self.generate_caption(topic=topic, tone=tone)
        if caption:
            result["caption"] = caption
            
            # Generate hashtags
            hashtags = self.generate_hashtags(caption, count=5)
            result["hashtags"] = hashtags
            result["full_text"] = f"{caption}\n\n{' '.join(hashtags)}"
        
        # Generate image(s) if requested
        if generate_image and post_type in ["image", "carousel"]:
            count = image_count if post_type == "carousel" else 1
            
            for i in range(count):
                # Generate optimized image prompt
                image_prompt = self.generate_image_prompt(
                    topic=topic,
                    style=style,
                    additional_context=f"Image {i+1} of {count}" if count > 1 else ""
                )
                
                if image_prompt:
                    # Generate the image
                    image_result = self.generate_image(prompt=image_prompt)
                    if image_result:
                        image_result["original_prompt"] = image_prompt
                        result["images"].append(image_result)
        
        return result
    
    def get_generated_images_dir(self) -> Path:
        """Return the path to the generated images directory."""
        return self.generated_images_dir
