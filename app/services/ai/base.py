from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PageAnalysisResult:
    executive_summary: str
    company_profile: str
    engagement_analysis: str
    audience_insights: str
    recommendations: List[str] = field(default_factory=list)
    provider: str = "unknown"
    model: str = "unknown"
    tokens_used: Optional[int] = None
    cached: bool = False


class BaseAIProvider(ABC):
    
    def __init__(self, api_key: str, model: str):
        self._api_key = api_key
        self._model = model
        self._initialized = False
    
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass
    
    @property
    def model_name(self) -> str:
        return self._model
    
    @abstractmethod
    async def initialize(self) -> None:
        pass
    
    @abstractmethod
    async def generate_content(self, prompt: str) -> Optional[str]:
        pass
    
    def is_available(self) -> bool:
        return self._initialized and bool(self._api_key)
    
    async def generate_page_analysis(
        self,
        page_data: Dict[str, Any],
        posts_data: Optional[List[Dict]] = None,
        employees_data: Optional[List[Dict]] = None,
    ) -> Optional[PageAnalysisResult]:
        if not self.is_available():
            return None
        
        prompt = self._build_prompt(page_data, posts_data, employees_data)
        
        response = await self.generate_content(prompt)
        
        if not response:
            return None
        
        return self._parse_response(response)
    
    def _build_prompt(
        self,
        page_data: Dict[str, Any],
        posts_data: Optional[List[Dict]] = None,
        employees_data: Optional[List[Dict]] = None,
    ) -> str:
        page_info = f"""
Company: {page_data.get('name', 'Unknown')}
Industry: {page_data.get('industry', 'Unknown')}
Follower Count: {page_data.get('follower_count', 0):,}
Company Type: {page_data.get('company_type', 'Unknown')}
Headquarters: {page_data.get('headquarters', 'Unknown')}
Founded: {page_data.get('founded', 'Unknown')}
Headcount: {page_data.get('headcount', 'Unknown')}
Specialities: {', '.join(page_data.get('specialities', []) or [])}
Description: {page_data.get('description', 'Not available')}
        """.strip()
        
        posts_info = ""
        if posts_data:
            posts_summary = []
            for post in posts_data[:5]:
                content = post.get('content', '')[:200] if post.get('content') else 'No content'
                posts_summary.append(f"""
- Content: {content}...
  Likes: {post.get('like_count', 0)}, Comments: {post.get('comment_count', 0)}, Shares: {post.get('share_count', 0)}
                """.strip())
            posts_info = f"\n\nRecent Posts:\n" + "\n".join(posts_summary)
        
        employees_info = ""
        if employees_data:
            emp_summary = [
                f"- {emp.get('name', 'Unknown')}: {emp.get('designation', 'Unknown')}"
                for emp in employees_data[:5]
            ]
            employees_info = f"\n\nKey Employees:\n" + "\n".join(emp_summary)
        
        return f"""You are a LinkedIn analytics expert. Analyze this company page data and provide a comprehensive summary.

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
    
    def _parse_response(self, response_text: str) -> PageAnalysisResult:
        import json
        
        try:
            text = response_text.strip()
            
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            
            data = json.loads(text.strip())
            
            return PageAnalysisResult(
                executive_summary=data.get("executive_summary", "Summary not available"),
                company_profile=data.get("company_profile", "Profile not available"),
                engagement_analysis=data.get("engagement_analysis", "Analysis not available"),
                audience_insights=data.get("audience_insights", "Insights not available"),
                recommendations=data.get("recommendations", []),
                provider=self.provider_name,
                model=self.model_name,
            )
            
        except json.JSONDecodeError as e:
            print(f"⚠️ Failed to parse AI response as JSON: {e}")
            return PageAnalysisResult(
                executive_summary=response_text[:500] if response_text else "Summary not available",
                company_profile="Could not parse structured response",
                engagement_analysis="Could not parse structured response",
                audience_insights="Could not parse structured response",
                recommendations=[],
                provider=self.provider_name,
                model=self.model_name,
            )
