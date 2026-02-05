"""
Image Rating Module using OpenAI's GPT-4 Vision
Rates images on creativity, art style, composition, and overall quality
"""

import base64
import json
from typing import Dict, List, Optional, Union
from pathlib import Path
import requests
from PIL import Image
import io

class ImageRater:
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        """
        Initialize the ImageRater with OpenAI API credentials
        
        Args:
            api_key: OpenAI API key
            model: Model to use (gpt-4o, gpt-4o-mini)
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        
    def encode_image(self, image_path: Union[str, Path]) -> str:
        """Encode image to base64"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def resize_image_if_needed(self, image_path: Union[str, Path], max_size: int = 1024) -> str:
        """Resize image if it's too large and return base64 encoded string"""
        with Image.open(image_path) as img:
            # Check if image needs resizing
            if max(img.size) > max_size:
                # Calculate new size maintaining aspect ratio
                ratio = max_size / max(img.size)
                new_size = tuple(int(dim * ratio) for dim in img.size)
                img = img.resize(new_size, Image.Resampling.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG")
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    def rate_image(self, 
                   image_path: Union[str, Path], 
                   categories: Optional[List[str]] = None,
                   scale: int = 10,
                   detailed_feedback: bool = True) -> Dict:
        """
        Rate an image on various criteria
        
        Args:
            image_path: Path to the image file
            categories: List of categories to rate (default: standard art categories)
            scale: Rating scale (1 to scale, default 10)
            detailed_feedback: Whether to include detailed explanations
            
        Returns:
            Dictionary with ratings and feedback
        """
        
        if categories is None:
            categories = [
                "creativity", 
                "art_style", 
                "composition", 
                "color_harmony", 
                "technical_skill",
                "emotional_impact",
                "originality"
            ]
        
        # Encode image
        base64_image = self.resize_image_if_needed(image_path)
        
        # Create prompt
        prompt = f"""
        Please rate this image on the following categories using a scale of 1-{scale}:
        
        Categories: {', '.join(categories)}
        
        For each category, provide:
        1. A numerical rating (1-{scale})
        2. {"A brief explanation of the rating" if detailed_feedback else ""}
        
        Also provide:
        - An overall rating (1-{scale})
        - {"General feedback and suggestions for improvement" if detailed_feedback else ""}
        
        Please respond in JSON format like this:
        {{
            "ratings": {{
                "category_name": {{"score": X, "explanation": "..."}},
                ...
            }},
            "overall_rating": {{"score": X, "explanation": "..."}},
            "summary": "Brief overall assessment"
        }}
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 1000
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to parse JSON response
            try:
                # Clean the content - remove markdown code blocks if present
                cleaned_content = content.strip()
                if cleaned_content.startswith('```json'):
                    cleaned_content = cleaned_content[7:]  # Remove ```json
                if cleaned_content.startswith('```'):
                    cleaned_content = cleaned_content[3:]   # Remove ```
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]  # Remove closing ```
                
                cleaned_content = cleaned_content.strip()
                parsed_result = json.loads(cleaned_content)
                return parsed_result
            except json.JSONDecodeError:
                # If JSON parsing fails, return raw content
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": content
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": f"API request failed: {str(e)}"
            }
    
    def rate_multiple_images(self, 
                           image_paths: List[Union[str, Path]], 
                           categories: Optional[List[str]] = None) -> Dict:
        """
        Rate multiple images and return comparative results
        
        Args:
            image_paths: List of paths to image files
            categories: List of categories to rate
            
        Returns:
            Dictionary with individual ratings and comparative analysis
        """
        results = {}
        
        for i, path in enumerate(image_paths):
            print(f"Rating image {i+1}/{len(image_paths)}: {Path(path).name}")
            results[f"image_{i+1}"] = {
                "path": str(path),
                "ratings": self.rate_image(path, categories)
            }
        
        return results
    
    def get_style_analysis(self, image_path: Union[str, Path]) -> Dict:
        """
        Get detailed style analysis of an image
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with style analysis
        """
        base64_image = self.resize_image_if_needed(image_path)
        
        prompt = """
        Please provide a detailed style analysis of this image. Include:
        
        1. Art style/movement (e.g., impressionism, photorealism, abstract, etc.)
        2. Medium/technique (digital art, oil painting, watercolor, etc.)
        3. Color palette description
        4. Lighting and mood
        5. Subject matter and themes
        6. Influences or similar artists/styles
        
        Respond in JSON format:
        {
            "style": "...",
            "medium": "...",
            "color_palette": "...",
            "lighting_mood": "...",
            "subject_themes": "...",
            "influences": "...",
            "overall_description": "..."
        }
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 800
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            try:
                # Clean the content - remove markdown code blocks if present
                cleaned_content = content.strip()
                if cleaned_content.startswith('```json'):
                    cleaned_content = cleaned_content[7:]  # Remove ```json
                if cleaned_content.startswith('```'):
                    cleaned_content = cleaned_content[3:]   # Remove ```
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]  # Remove closing ```
                
                cleaned_content = cleaned_content.strip()
                return json.loads(cleaned_content)
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": content
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": f"API request failed: {str(e)}"
            }

    def get_image_description(self, image_path: Union[str, Path]) -> Dict:
        """
        Get a highly structured marketing-focused description of the image.
        
        The response is designed to capture both visual DNA and strategic
        analysis for ad creative, and is returned in the following JSON schema:
        
        {
            "visual_dna": {
                "composition": "...",
                "palette": "...",
                "lighting": "...",
                "style": "..."
            },
            "strategic_analysis": {
                "tone": "...",
                "cta_style": "...",
                "emotional_angle": "...",
                "audience": "..."
            },
            "image_composition_analysis": {
                "focal_points": "...",
                "typography_style": "..."
            },
            "prompt_reconstruction": "..."
        }
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary matching the schema above
        """
        base64_image = self.resize_image_if_needed(image_path)
        
        prompt = """
        You are an expert creative strategist and visual analyst for performance
        marketing. Analyze this image and return a JSON object that captures its
        \"visual DNA\", strategic role, and a reconstruction prompt.
        
        Use this exact JSON schema (keys must match exactly; values are examples,
        not templates to reuse):
        
        {
            "visual_dna": {
                "composition": "Hero-centered with dynamic diagonal lines",
                "palette": "Bold orange (#FF6B35) 45%, Navy (#004E89) 30%, plus supporting neutrals",
                "lighting": "High contrast studio lighting",
                "style": "Premium, athletic, modern minimalism"
            },
            "strategic_analysis": {
                "tone": "Confident, aspirational, energetic",
                "cta_style": "Direct action with urgency",
                "emotional_angle": "Performance & achievement",
                "audience": "Active lifestyle, 25-45, performance-driven"
            },
            "image_composition_analysis": {
                "focal_points": "Primary focus on product with ~60% saliency; secondary background elements create depth",
                "typography_style": "Bold sans-serif headlines, minimal copy, high contrast for legibility"
            },
            "prompt_reconstruction": "Professional product photography, athletic shoe on gradient background, dramatic studio lighting, high contrast, bold orange and navy color scheme, modern minimalist composition, commercial advertising style --ar 1:1 --style raw"
        }
        
        Instructions:
        - Keep the same structure and keys.
        - Replace all example values with descriptions that accurately reflect THIS image.
        - Use concise but information-dense language.
        - Make "prompt_reconstruction" directly usable as an image generation prompt.
        - Respond with VALID JSON only (no markdown code fences or extra text).
        """
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            try:
                # Clean the content - remove markdown code blocks if present
                cleaned_content = content.strip()
                if cleaned_content.startswith('```json'):
                    cleaned_content = cleaned_content[7:]  # Remove ```json
                if cleaned_content.startswith('```'):
                    cleaned_content = cleaned_content[3:]   # Remove ```
                if cleaned_content.endswith('```'):
                    cleaned_content = cleaned_content[:-3]  # Remove closing ```
                
                cleaned_content = cleaned_content.strip()
                return json.loads(cleaned_content)
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse JSON response",
                    "raw_response": content
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "error": f"API request failed: {str(e)}"
            }

    def generate_image_dalle(self, prompt: str, output_path: Union[str, Path], size: str = "1024x1024", quality: str = "standard") -> Dict:
        """
        Generate an image using DALL-E 3 based on the prompt
        
        Args:
            prompt: Text prompt for generation
            output_path: Path to save the generated image
            size: Size of the image (default 1024x1024)
            quality: Quality of the image (standard or hd)
            
        Returns:
            Dictionary with result info
        """
        print(f"Generating image with prompt: {prompt[:50]}...")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "response_format": "b64_json"
        }
        
        try:
            response = requests.post("https://api.openai.com/v1/images/generations", headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            image_data = result['data'][0]['b64_json']
            
            # Save image
            with open(output_path, "wb") as f:
                f.write(base64.b64decode(image_data))
                
            return {
                "success": True,
                "path": str(output_path),
                "revised_prompt": result['data'][0].get('revised_prompt', prompt)
            }
                
        except requests.exceptions.RequestException as e:
            error_msg = f"DALL-E API request failed: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_msg += f" - {e.response.text}"
            return {
                "success": False,
                "error": error_msg
            }


# Example usage
if __name__ == "__main__":
    import os
    # Initialize the rater with API key from environment
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set. Please add it to your .env file.")
    rater = ImageRater(api_key=api_key)
    
    # Rate a single image
    result = rater.rate_image("D:/SAMODREI/Instagram/TRIAL/633c0e1fa0bfc267ebe5c4b07140430d.jpg")
    print("Rating Results:")
    print(json.dumps(result, indent=2))
    
    # Get style analysis
    style_analysis = rater.get_style_analysis("D:/SAMODREI/Instagram/TRIAL/633c0e1fa0bfc267ebe5c4b07140430d.jpg")
    print("\nStyle Analysis:")
    print(json.dumps(style_analysis, indent=2))
    
    # Rate multiple images
    # results = rater.rate_multiple_images([
    #     "image1.jpg",
    #     "image2.jpg",
    #     "image3.jpg"
    # ])
    
    # Custom categories example
    custom_categories = ["realism", "innovation", "visual_appeal", "storytelling"]
    custom_result = rater.rate_image("D:/SAMODREI/Instagram/TRIAL/633c0e1fa0bfc267ebe5c4b07140430d.jpg", categories=custom_categories)