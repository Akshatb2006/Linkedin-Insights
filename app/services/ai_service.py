import json
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.config import get_settings


@dataclass
class PageSummary:
    executive_summary: str
    company_profile: str
    engagement_analysis: str
    audience_insights: str
    recommendations: list[str]
    generated_by: str = "gemini-1.5-flash"


class AIService:
    _client = None
    _model = None
    
    @classmethod
    def _get_client(cls):
        if cls._client is None:
            settings = get_settings()
            if not settings.is_ai_enabled:
                return None
            
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.gemini_api_key)
                cls._client = genai
                cls._model = genai.GenerativeModel(settings.ai_model)
            except Exception as e:
                print(f"⚠️ Failed to initialize Gemini: {e}")
                return None
        
        return cls._client
    
    @classmethod
    async def generate_page_summary(
        cls,
        page_data: Dict[str, Any],
        posts_data: list = None,
        employees_data: list = None,
    ) -> Optional[PageSummary]:
        settings = get_settings()
        
        if not settings.is_ai_enabled:
            return None
        
        client = cls._get_client()
        if not client or cls._model is None:
            return None
        
        prompt = cls._build_prompt(page_data, posts_data, employees_data)
        
        try:
            response = cls._model.generate_content(prompt)
            
            return cls._parse_response(response.text)
            
        except Exception as e:
            print(f"❌ AI generation error: {e}")
            return None
    
    @classmethod
    def _build_prompt(
        cls,
        page_data: Dict[str, Any],
        posts_data: list = None,
        employees_data: list = None,
    ) -> str:
        page_info = f"""
Company: {page_data.get('name', 'Unknown')}
Industry: {page_data.get('industry', 'Unknown')}
Follower Count: {page_data.get('follower_count', 0):,}
Company Type: {page_data.get('company_type', 'Unknown')}
Headquarters: {page_data.get('headquarters', 'Unknown')}
Founded: {page_data.get('founded', 'Unknown')}
Headcount: {page_data.get('headcount', 'Unknown')}
Specialities: {', '.join(page_data.get('specialities', []))}
Description: {page_data.get('description', 'Not available')}
        """.strip()
        
        posts_info = ""
        if posts_data:
            posts_summary = []
            for post in posts_data[:5]:  
                posts_summary.append(f"""
- Content: {post.get('content', '')[:200]}...
  Likes: {post.get('like_count', 0)}, Comments: {post.get('comment_count', 0)}, Shares: {post.get('share_count', 0)}
                """.strip())
            posts_info = f"\n\nRecent Posts:\n" + "\n".join(posts_summary)
        
        employees_info = ""
        if employees_data:
            emp_summary = [f"- {emp.get('name', 'Unknown')}: {emp.get('designation', 'Unknown')}" 
                          for emp in employees_data[:5]]
            employees_info = f"\n\nKey Employees:\n" + "\n".join(emp_summary)
        
        prompt = f"""You are a LinkedIn analytics expert. Analyze this company page data and provide a comprehensive summary.

{page_info}
{posts_info}
{employees_info}

Please provide your analysis in the following JSON format:
{{
    "executive_summary": "A 2-3 sentence overview of the company's LinkedIn presence",
    "company_profile": "Brief analysis of the company type, industry position, and size",
    "engagement_analysis": "Analysis of their content engagement based on likes, comments, shares",
    "audience_insights": "Insights about their likely audience based on follower count and content type",
    "recommendations": ["Recommendation 1", "Recommendation 2", "Recommendation 3"]
}}

Respond ONLY with the JSON object, no additional text."""
        
        return prompt
    
    @classmethod
    def _parse_response(cls, response_text: str) -> PageSummary:
        try:
            text = response_text.strip()
            
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text.strip())
            
            return PageSummary(
                executive_summary=data.get("executive_summary", "Summary not available"),
                company_profile=data.get("company_profile", "Profile not available"),
                engagement_analysis=data.get("engagement_analysis", "Analysis not available"),
                audience_insights=data.get("audience_insights", "Insights not available"),
                recommendations=data.get("recommendations", []),
                generated_by="gemini-1.5-flash"
            )
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse AI response as JSON: {e}")
            return PageSummary(
                executive_summary=response_text[:500] if response_text else "Summary not available",
                company_profile="Could not parse structured response",
                engagement_analysis="Could not parse structured response",
                audience_insights="Could not parse structured response",
                recommendations=[],
                generated_by="gemini-1.5-flash"
            )
