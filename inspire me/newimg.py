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

    def transform_image_with_reference(
        self,
        base_image_path: Union[str, Path],
        reference_image_path: Union[str, Path],
        prompt: str,
        output_path: Union[str, Path],
        size: str = "1024x1024",
        transformation_instructions: Optional[str] = None
    ) -> Dict:
        """
        Transform a base image using a reference image and prompt with gpt-image-1.
        
        This method takes an original image (base), a reference image, and a prompt
        to generate a new image that combines elements from both according to the prompt.
        
        Args:
            base_image_path: Path to the original/base image
            reference_image_path: Path to the reference image to incorporate
            prompt: The transformation prompt (e.g., from prompt_reconstruction)
            output_path: Path to save the generated image
            size: Size of output image (default 1024x1024)
            transformation_instructions: Optional specific instructions for the transformation
            
        Returns:
            Dictionary with result info including success status and path
        """
        print(f"Transforming image with reference...")
        print(f"  Base image: {base_image_path}")
        print(f"  Reference image: {reference_image_path}")
        print(f"  Prompt: {prompt[:100]}...")
        
        # Encode both images to base64
        base_image_b64 = self.encode_image(base_image_path)
        reference_image_b64 = self.encode_image(reference_image_path)
        
        # Build the transformation prompt
        if transformation_instructions:
            full_prompt = f"""
{transformation_instructions}

Base creative style and composition guidance:
{prompt}

Instructions:
- Use the first image as the base composition and style reference
- Incorporate elements from the second (reference) image as specified
- Preserve lighting, shadows, reflections, and camera angle from the base
- Maintain the overall aesthetic and brand feel
- Do not change elements that aren't specifically mentioned
"""
        else:
            full_prompt = f"""
Using the provided images as references, create a new creative that:
- Follows the composition and style of the first image (base)
- Incorporates or is inspired by elements from the second image (reference)
- Maintains professional commercial quality

Creative brief:
{prompt}

Preserve lighting, shadows, reflections, camera angle, and background style.
Create a cohesive, polished final result suitable for advertising.
"""
        
        try:
            # Use OpenAI Responses API with image_generation tool
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            
            # Read both images and convert to base64 data URLs
            base_path = Path(base_image_path)
            ref_path = Path(reference_image_path)
            
            # Create base64 data URLs for both images
            with open(base_path, "rb") as f:
                base_b64 = base64.b64encode(f.read()).decode('utf-8')
            with open(ref_path, "rb") as f:
                ref_b64 = base64.b64encode(f.read()).decode('utf-8')
            
            # Determine image types
            base_ext = base_path.suffix.lower().replace('.', '')
            ref_ext = ref_path.suffix.lower().replace('.', '')
            base_mime = f"image/{base_ext}" if base_ext in ['png', 'jpg', 'jpeg', 'gif', 'webp'] else "image/jpeg"
            ref_mime = f"image/{ref_ext}" if ref_ext in ['png', 'jpg', 'jpeg', 'gif', 'webp'] else "image/jpeg"
            
            base_data_url = f"data:{base_mime};base64,{base_b64}"
            ref_data_url = f"data:{ref_mime};base64,{ref_b64}"
            
            # Use Responses API with image_generation tool
            response = client.responses.create(
                model="gpt-4.1",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": full_prompt},
                            {
                                "type": "input_image",
                                "image_url": base_data_url,
                            },
                            {
                                "type": "input_image",
                                "image_url": ref_data_url,
                            },
                        ],
                    }
                ],
                tools=[{"type": "image_generation", "input_fidelity": "high", "action": "edit"}],
            )
            
            # Extract the edited image
            image_data = [
                output.result
                for output in response.output
                if output.type == "image_generation_call"
            ]
            
            if image_data:
                image_base64 = image_data[0]
                
                # Save output
                output_path = Path(output_path)
                with open(output_path, "wb") as f:
                    f.write(base64.b64decode(image_base64))
                
                print(f"  ✅ Image saved to: {output_path}")
                
                return {
                    "success": True,
                    "path": str(output_path),
                    "prompt_used": full_prompt[:500] + "..." if len(full_prompt) > 500 else full_prompt
                }
            else:
                return {
                    "success": False,
                    "error": "No image generated in response"
                }
            
        except Exception as e:
            error_msg = f"gpt-image-1 transformation failed: {str(e)}"
            print(f"  ❌ Error: {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

    def transform_from_analysis(
        self,
        base_image_path: Union[str, Path],
        reference_image_path: Union[str, Path],
        analysis_json: Dict,
        output_path: Union[str, Path],
        size: str = "1024x1024",
        custom_instructions: Optional[str] = None
    ) -> Dict:
        """
        Transform an image using a reference and analysis data from get_image_description.
        
        This is a convenience method that extracts the prompt_reconstruction from
        the analysis JSON and uses it for the transformation.
        
        Args:
            base_image_path: Path to the original/base image
            reference_image_path: Path to the reference image
            analysis_json: Analysis data from get_image_description() containing prompt_reconstruction
            output_path: Path to save the generated image
            size: Size of output image
            custom_instructions: Optional additional instructions for transformation
            
        Returns:
            Dictionary with result info
        """
        # Extract prompt from analysis
        prompt = analysis_json.get("prompt_reconstruction", "")
        
        if not prompt:
            return {
                "success": False,
                "error": "No prompt_reconstruction found in analysis JSON"
            }
        
        # Build enhanced instructions if we have visual DNA
        transformation_instructions = None
        if "visual_dna" in analysis_json:
            vd = analysis_json["visual_dna"]
            transformation_instructions = f"""
Create a new image that combines elements from both provided images.

Visual DNA to preserve from base:
- Composition: {vd.get('composition', 'N/A')}
- Color Palette: {vd.get('palette', 'N/A')}
- Lighting: {vd.get('lighting', 'N/A')}
- Style: {vd.get('style', 'N/A')}
"""
            if custom_instructions:
                transformation_instructions += f"\nAdditional instructions: {custom_instructions}"
        
        return self.transform_image_with_reference(
            base_image_path=base_image_path,
            reference_image_path=reference_image_path,
            prompt=prompt,
            output_path=output_path,
            size=size,
            transformation_instructions=transformation_instructions
        )


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