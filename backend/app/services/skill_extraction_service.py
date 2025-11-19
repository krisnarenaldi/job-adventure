"""
Skill extraction and matching service for identifying and comparing skills
between job descriptions and resumes using keyword matching and spaCy NLP.
"""

import logging
import re
from typing import List, Dict, Set, Any, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
from pydantic import BaseModel, ConfigDict

logger = logging.getLogger(__name__)


class SkillMatch(BaseModel):
    """Result of skill matching between job and resume."""
    matched_skills: List[str] 
    missing_skills: List[str]
    additional_skills: List[str]  # Skills in resume but not required by job
    match_percentage: float
    skill_categories: Dict[str, List[str]]

    model_config = ConfigDict(from_attributes=True)


class SkillAnalysis(BaseModel):
    """Detailed analysis of skills in a document."""
    technical_skills: List[str] = []
    soft_skills: List[str] = []
    tools_and_technologies: List[str] = []
    certifications: List[str] = []
    all_skills: List[str] = []
    confidence_scores: Dict[str, float] = {}
    
    model_config = ConfigDict(from_attributes=True)


class SkillExtractionService:
    """Service for extracting and matching skills from text documents."""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._nlp_model = None
        self._skill_database = None
        self._initialized = False
        
        # Predefined skill categories and patterns
        self.technical_skills_patterns = [
            # Programming languages
            r'\b(?:python|java|javascript|typescript|c\+\+|c#|php|ruby|go|rust|swift|kotlin|scala|r|matlab)\b',
            # Web technologies
            r'\b(?:html|css|react|angular|vue|node\.?js|express|django|flask|spring|laravel)\b',
            # Databases
            r'\b(?:sql|mysql|postgresql|mongodb|redis|elasticsearch|oracle|sqlite)\b',
            # Cloud platforms
            r'\b(?:aws|azure|gcp|google cloud|docker|kubernetes|terraform|ansible)\b',
            # Data science
            r'\b(?:pandas|numpy|scikit-learn|tensorflow|pytorch|spark|hadoop|tableau|power bi)\b',
            # DevOps
            r'\b(?:git|jenkins|ci/cd|linux|bash|shell scripting|nginx|apache)\b'
        ]
        
        self.soft_skills_patterns = [
            r'\b(?:leadership|communication|teamwork|problem solving|analytical|creative)\b',
            r'\b(?:project management|time management|critical thinking|adaptability)\b',
            r'\b(?:collaboration|presentation|negotiation|mentoring|coaching)\b'
        ]
        
        self.certification_patterns = [
            r'\b(?:aws certified|azure certified|google cloud certified|pmp|scrum master)\b',
            r'\b(?:cissp|comptia|cisco|microsoft certified|oracle certified)\b'
        ]
        
        # Common skill synonyms and variations
        self.skill_synonyms = {
            'javascript': ['js', 'ecmascript'],
            'typescript': ['ts'],
            'python': ['py'],
            'postgresql': ['postgres', 'psql'],
            'mongodb': ['mongo'],
            'node.js': ['nodejs', 'node'],
            'react.js': ['react', 'reactjs'],
            'angular.js': ['angular', 'angularjs'],
            'vue.js': ['vue', 'vuejs'],
            'machine learning': ['ml', 'artificial intelligence', 'ai'],
            'deep learning': ['dl', 'neural networks'],
            'natural language processing': ['nlp'],
            'computer vision': ['cv'],
            'devops': ['dev ops', 'development operations'],
            'ci/cd': ['continuous integration', 'continuous deployment'],
            'rest api': ['restful api', 'rest', 'api'],
            'graphql': ['graph ql'],
            'microservices': ['micro services'],
            'agile': ['scrum', 'kanban'],
            'project management': ['pm', 'program management']
        }
    
    async def initialize(self):
        """Initialize spaCy model and skill database."""
        if self._initialized:
            return
            
        try:
            # Try to load spaCy model
            try:
                import spacy
                logger.info("Loading spaCy model...")
                # Importing spaCy can trigger imports that rely on pydantic v1; on
                # Python 3.12 some older pydantic.v1 code may raise TypeError during
                # evaluation of ForwardRefs. Catch any exception here and fall back
                # to pattern-based extraction so service initialization doesn't fail.
                self._nlp_model = spacy.load("en_core_web_sm")
                logger.info("spaCy model loaded successfully")
            except Exception as e:
                # Catch all exceptions so a problematic third-party import (e.g.,
                # pydantic.v1 incompatibility) won't crash service startup.
                logger.warning(
                    f"spaCy model not available or failed to initialize: {type(e).__name__}: {e}. Using pattern-based extraction only."
                )
                self._nlp_model = None
            
            # Load or create skill database
            await self._load_skill_database()
            
            self._initialized = True
            logger.info("Skill extraction service initialized")
            
        except Exception as e:
            logger.exception(f"Failed to initialize skill extraction service: {e}")
            raise
    
    async def _load_skill_database(self):
        """Load comprehensive skill database."""
        # This would typically load from a file or database
        # For now, we'll use a basic in-memory database
        self._skill_database = {
            'technical_skills': [
                # Programming Languages
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust',
                'swift', 'kotlin', 'scala', 'r', 'matlab', 'sql', 'html', 'css',
                
                # Frameworks and Libraries
                'react', 'angular', 'vue', 'node.js', 'express', 'django', 'flask', 'spring', 'laravel',
                'bootstrap', 'jquery', 'pandas', 'numpy', 'scikit-learn', 'tensorflow', 'pytorch',
                
                # Databases
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sqlite', 'cassandra',
                
                # Cloud and DevOps
                'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'terraform', 'ansible', 'jenkins',
                'git', 'linux', 'bash', 'nginx', 'apache',
                
                # Data Science and Analytics
                'machine learning', 'deep learning', 'data analysis', 'statistics', 'tableau', 'power bi',
                'spark', 'hadoop', 'etl', 'data mining', 'predictive modeling',
                
                # Mobile Development
                'ios', 'android', 'react native', 'flutter', 'xamarin',
                
                # Testing
                'unit testing', 'integration testing', 'selenium', 'jest', 'pytest', 'junit'
            ],
            
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving', 'analytical thinking',
                'creative thinking', 'project management', 'time management', 'critical thinking',
                'adaptability', 'collaboration', 'presentation skills', 'negotiation', 'mentoring',
                'coaching', 'strategic planning', 'decision making', 'conflict resolution',
                'customer service', 'sales', 'marketing', 'business development'
            ],
            
            'certifications': [
                'aws certified', 'azure certified', 'google cloud certified', 'pmp', 'scrum master',
                'cissp', 'comptia', 'cisco certified', 'microsoft certified', 'oracle certified',
                'certified kubernetes administrator', 'certified ethical hacker', 'six sigma'
            ]
        }
    
    def _normalize_skill(self, skill: str) -> str:
        """Normalize skill name for consistent matching."""
        skill = skill.lower().strip()
        
        # Handle common variations
        for canonical, variations in self.skill_synonyms.items():
            if skill in variations or skill == canonical:
                return canonical
        
        return skill
    
    def _extract_skills_by_patterns(self, text: str) -> SkillAnalysis:
        """Extract skills using regex patterns."""
        text_lower = text.lower()
        
        technical_skills = set()
        soft_skills = set()
        certifications = set()
        
        # Extract technical skills
        for pattern in self.technical_skills_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            technical_skills.update(self._normalize_skill(match) for match in matches)
        
        # Extract soft skills
        for pattern in self.soft_skills_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            soft_skills.update(self._normalize_skill(match) for match in matches)
        
        # Extract certifications
        for pattern in self.certification_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            certifications.update(self._normalize_skill(match) for match in matches)
        
        # Also check against skill database
        if self._skill_database:
            for skill in self._skill_database['technical_skills']:
                if skill.lower() in text_lower:
                    technical_skills.add(skill)
            
            for skill in self._skill_database['soft_skills']:
                if skill.lower() in text_lower:
                    soft_skills.add(skill)
            
            for cert in self._skill_database['certifications']:
                if cert.lower() in text_lower:
                    certifications.add(cert)
        
        all_skills = list(technical_skills | soft_skills | certifications)
        
        return SkillAnalysis(
            technical_skills=list(technical_skills),
            soft_skills=list(soft_skills),
            tools_and_technologies=list(technical_skills),  # For now, same as technical
            certifications=list(certifications),
            all_skills=all_skills,
            confidence_scores={skill: 0.8 for skill in all_skills}  # Pattern-based confidence
        )
    
    def _extract_skills_with_spacy(self, text: str) -> SkillAnalysis:
        """Extract skills using spaCy NLP model."""
        if not self._nlp_model:
            return self._extract_skills_by_patterns(text)
        
        try:
            doc = self._nlp_model(text)
            
            # Extract entities and noun phrases that might be skills
            potential_skills = set()
            
            # Named entities
            for ent in doc.ents:
                if ent.label_ in ['ORG', 'PRODUCT', 'LANGUAGE']:  # Organizations, products, languages
                    potential_skills.add(ent.text.lower())
            
            # Noun phrases
            for chunk in doc.noun_chunks:
                if len(chunk.text.split()) <= 3:  # Limit to reasonable skill length
                    potential_skills.add(chunk.text.lower())
            
            # Filter against known skills
            technical_skills = set()
            soft_skills = set()
            certifications = set()
            
            if self._skill_database:
                for skill in potential_skills:
                    normalized_skill = self._normalize_skill(skill)
                    
                    if normalized_skill in [s.lower() for s in self._skill_database['technical_skills']]:
                        technical_skills.add(normalized_skill)
                    elif normalized_skill in [s.lower() for s in self._skill_database['soft_skills']]:
                        soft_skills.add(normalized_skill)
                    elif normalized_skill in [s.lower() for s in self._skill_database['certifications']]:
                        certifications.add(normalized_skill)
            
            # Combine with pattern-based extraction for better coverage
            pattern_results = self._extract_skills_by_patterns(text)
            technical_skills.update(pattern_results.technical_skills)
            soft_skills.update(pattern_results.soft_skills)
            certifications.update(pattern_results.certifications)
            
            all_skills = list(technical_skills | soft_skills | certifications)
            
            return SkillAnalysis(
                technical_skills=list(technical_skills),
                soft_skills=list(soft_skills),
                tools_and_technologies=list(technical_skills),
                certifications=list(certifications),
                all_skills=all_skills,
                confidence_scores={skill: 0.9 for skill in all_skills}  # Higher confidence with NLP
            )
            
        except Exception as e:
            logger.error(f"Error in spaCy skill extraction: {e}")
            return self._extract_skills_by_patterns(text)
    
    async def extract_skills(self, text: str) -> SkillAnalysis:
        """
        Extract skills from text using available methods.
        
        Args:
            text: Input text to analyze
            
        Returns:
            SkillAnalysis with categorized skills
        """
        if not self._initialized:
            await self.initialize()
        
        if not text or not text.strip():
            return SkillAnalysis(
                technical_skills=[],
                soft_skills=[],
                tools_and_technologies=[],
                certifications=[],
                all_skills=[],
                confidence_scores={}
            )
        
        try:
            # Run skill extraction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            if self._nlp_model:
                result = await loop.run_in_executor(
                    self.executor,
                    self._extract_skills_with_spacy,
                    text
                )
            else:
                result = await loop.run_in_executor(
                    self.executor,
                    self._extract_skills_by_patterns,
                    text
                )
            
            logger.debug(f"Extracted {len(result.all_skills)} skills from text")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting skills: {e}")
            return SkillAnalysis(
                technical_skills=[],
                soft_skills=[],
                tools_and_technologies=[],
                certifications=[],
                all_skills=[],
                confidence_scores={}
            )
    
    def compare_skills(self, job_skills: List[str], resume_skills: List[str]) -> SkillMatch:
        """
        Compare skills between job requirements and resume.
        
        Args:
            job_skills: Skills required by the job
            resume_skills: Skills present in the resume
            
        Returns:
            SkillMatch with detailed comparison
        """
        try:
            # Normalize all skills for comparison
            job_skills_normalized = {self._normalize_skill(skill) for skill in job_skills}
            resume_skills_normalized = {self._normalize_skill(skill) for skill in resume_skills}
            
            # Find matches and gaps
            matched_skills = list(job_skills_normalized & resume_skills_normalized)
            missing_skills = list(job_skills_normalized - resume_skills_normalized)
            additional_skills = list(resume_skills_normalized - job_skills_normalized)
            
            # Calculate match percentage
            if job_skills_normalized:
                match_percentage = (len(matched_skills) / len(job_skills_normalized)) * 100
            else:
                match_percentage = 0.0
            
            # Categorize skills
            skill_categories = {
                'matched': matched_skills,
                'missing': missing_skills,
                'additional': additional_skills
            }
            
            return SkillMatch(
                matched_skills=matched_skills,
                missing_skills=missing_skills,
                additional_skills=additional_skills,
                match_percentage=round(match_percentage, 2),
                skill_categories=skill_categories
            )
            
        except Exception as e:
            logger.error(f"Error comparing skills: {e}")
            return SkillMatch(
                matched_skills=[],
                missing_skills=job_skills,
                additional_skills=[],
                match_percentage=0.0,
                skill_categories={'matched': [], 'missing': job_skills, 'additional': []}
            )
    
    async def analyze_skill_gaps(self, job_text: str, resume_text: str) -> Dict[str, Any]:
        """
        Perform comprehensive skill gap analysis.
        
        Args:
            job_text: Job description text
            resume_text: Resume text
            
        Returns:
            Detailed skill gap analysis
        """
        try:
            # Extract skills from both documents
            job_analysis = await self.extract_skills(job_text)
            resume_analysis = await self.extract_skills(resume_text)
            
            # Compare skills
            skill_match = self.compare_skills(job_analysis.all_skills, resume_analysis.all_skills)
            
            # Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(skill_match.missing_skills)
            
            return {
                'job_skills': {
                    'technical': job_analysis.technical_skills,
                    'soft': job_analysis.soft_skills,
                    'certifications': job_analysis.certifications,
                    'total_count': len(job_analysis.all_skills)
                },
                'resume_skills': {
                    'technical': resume_analysis.technical_skills,
                    'soft': resume_analysis.soft_skills,
                    'certifications': resume_analysis.certifications,
                    'total_count': len(resume_analysis.all_skills)
                },
                'skill_match': {
                    'matched_skills': skill_match.matched_skills,
                    'missing_skills': skill_match.missing_skills,
                    'additional_skills': skill_match.additional_skills,
                    'match_percentage': skill_match.match_percentage,
                    'matched_count': len(skill_match.matched_skills),
                    'missing_count': len(skill_match.missing_skills)
                },
                'improvement_suggestions': improvement_suggestions,
                'analysis_metadata': {
                    'job_confidence': sum(job_analysis.confidence_scores.values()) / len(job_analysis.confidence_scores) if job_analysis.confidence_scores else 0,
                    'resume_confidence': sum(resume_analysis.confidence_scores.values()) / len(resume_analysis.confidence_scores) if resume_analysis.confidence_scores else 0,
                    'extraction_method': 'spacy' if self._nlp_model else 'patterns'
                }
            }
            
        except Exception as e:
            logger.error(f"Error in skill gap analysis: {e}")
            return {
                'error': str(e),
                'job_skills': {'technical': [], 'soft': [], 'certifications': [], 'total_count': 0},
                'resume_skills': {'technical': [], 'soft': [], 'certifications': [], 'total_count': 0},
                'skill_match': {'matched_skills': [], 'missing_skills': [], 'additional_skills': [], 'match_percentage': 0.0},
                'improvement_suggestions': [],
                'analysis_metadata': {'error': True}
            }
    
    def _generate_improvement_suggestions(self, missing_skills: List[str]) -> List[str]:
        """Generate suggestions for improving skills based on gaps."""
        suggestions = []
        
        if not missing_skills:
            return ["Great! You have all the required skills for this position."]
        
        # Categorize missing skills
        technical_missing = []
        soft_missing = []
        cert_missing = []
        
        if self._skill_database:
            for skill in missing_skills:
                if skill in [s.lower() for s in self._skill_database['technical_skills']]:
                    technical_missing.append(skill)
                elif skill in [s.lower() for s in self._skill_database['soft_skills']]:
                    soft_missing.append(skill)
                elif skill in [s.lower() for s in self._skill_database['certifications']]:
                    cert_missing.append(skill)
        
        # Generate specific suggestions
        if technical_missing:
            suggestions.append(f"Consider learning these technical skills: {', '.join(technical_missing[:5])}")
            if 'python' in technical_missing or 'javascript' in technical_missing:
                suggestions.append("Online platforms like Codecademy, freeCodeCamp, or Coursera offer excellent programming courses")
        
        if soft_missing:
            suggestions.append(f"Develop these soft skills: {', '.join(soft_missing[:3])}")
            suggestions.append("Consider taking leadership courses or joining professional organizations to develop soft skills")
        
        if cert_missing:
            suggestions.append(f"Consider obtaining these certifications: {', '.join(cert_missing[:3])}")
        
        # General suggestions
        if len(missing_skills) > 5:
            suggestions.append("Focus on the most critical skills first, then gradually build up the others")
        
        suggestions.append("Update your resume to highlight relevant projects and experiences that demonstrate these skills")
        
        return suggestions[:5]  # Limit to 5 suggestions
    
    async def close(self):
        """Clean up resources."""
        self.executor.shutdown(wait=True)
        logger.info("Skill extraction service executor shut down")


# Global skill extraction service instance
skill_extraction_service = SkillExtractionService()


async def get_skill_extraction_service() -> SkillExtractionService:
    """Dependency injection for skill extraction service."""
    if not skill_extraction_service._initialized:
        await skill_extraction_service.initialize()
    return skill_extraction_service