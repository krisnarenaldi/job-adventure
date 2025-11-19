import re
import logging
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, ConfigDict
from enum import Enum


logger = logging.getLogger(__name__)


class ResumeSection(str, Enum):
    """Enumeration of resume sections"""
    CONTACT = "contact"
    SUMMARY = "summary"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    SKILLS = "skills"
    PROJECTS = "projects"
    CERTIFICATIONS = "certifications"
    LANGUAGES = "languages"
    AWARDS = "awards"
    REFERENCES = "references"
    OTHER = "other"


from pydantic import BaseModel

class ExtractedSection(BaseModel):
    """Container for holding processed resume sections with positional information for further processing"""
    section_type: ResumeSection
    title: str
    content: str
    start_position: int
    end_position: int
    confidence: float

    model_config = ConfigDict(from_attributes=True)


class ParsedResume(BaseModel):
    """Data model for parsed resume content"""
    raw_text: str
    sections: List[ExtractedSection]
    metadata: Dict[str, Any]
    extracted_skills: List[str]
    confidence_score: float

    model_config = ConfigDict(from_attributes=True)


class ResumeParsingError(Exception):
    """Custom exception for resume parsing errors"""
    pass


class ResumeParser:
    """Service for parsing and extracting structured data from resume text"""
    
    def __init__(self):
        # Define section header patterns with variations
        self.section_patterns = {
            ResumeSection.CONTACT: [
                r'contact\s+information',
                r'personal\s+information',
                r'contact\s+details',
                r'contact',
            ],
            ResumeSection.SUMMARY: [
                r'professional\s+summary',
                r'career\s+summary',
                r'executive\s+summary',
                r'profile',
                r'summary',
                r'objective',
                r'career\s+objective',
                r'professional\s+objective',
            ],
            ResumeSection.EXPERIENCE: [
                r'work\s+experience',
                r'professional\s+experience',
                r'employment\s+history',
                r'career\s+history',
                r'experience',
                r'employment',
                r'work\s+history',
            ],
            ResumeSection.EDUCATION: [
                r'education',
                r'educational\s+background',
                r'academic\s+background',
                r'qualifications',
                r'academic\s+qualifications',
            ],
            ResumeSection.SKILLS: [
                r'technical\s+skills',
                r'core\s+competencies',
                r'key\s+skills',
                r'skills',
                r'competencies',
                r'expertise',
                r'proficiencies',
            ],
            ResumeSection.PROJECTS: [
                r'projects',
                r'key\s+projects',
                r'notable\s+projects',
                r'project\s+experience',
            ],
            ResumeSection.CERTIFICATIONS: [
                r'certifications',
                r'certificates',
                r'professional\s+certifications',
                r'licenses',
                r'credentials',
            ],
            ResumeSection.LANGUAGES: [
                r'languages',
                r'language\s+skills',
                r'linguistic\s+skills',
            ],
            ResumeSection.AWARDS: [
                r'awards',
                r'honors',
                r'achievements',
                r'recognition',
                r'awards\s+and\s+honors',
            ],
            ResumeSection.REFERENCES: [
                r'references',
                r'professional\s+references',
            ]
        }
        
        # Common section delimiters
        self.section_delimiters = [
            r'^\s*[A-Z\s]{3,}\s*$',  # ALL CAPS headers
            r'^\s*[A-Z][a-z\s]+\s*$',  # Title case headers
            r'^\s*[-=]{3,}\s*$',  # Horizontal lines
            r'^\s*\*{3,}\s*$',  # Asterisk lines
        ]
    
    async def extract_sections(self, resume_text: str) -> Dict[str, str]:
        """
        Extract structured sections from resume text.
        
        Args:
            resume_text: Raw resume text
            
        Returns:
            Dictionary mapping section names to their content

        Note:
            Use parse_resume() for getting a full ParsedResume model
        """
        if not resume_text or not resume_text.strip():
            raise ResumeParsingError("Resume text is empty or invalid")
        
        try:
            # Normalize text for processing
            normalized_text = self._normalize_text_for_parsing(resume_text)
            
            # Find section boundaries
            sections = self._identify_sections(normalized_text)
            
            # Extract content for each section
            extracted_sections = {}
            for section in sections:
                content = self._extract_section_content(
                    normalized_text, 
                    section.start_position, 
                    section.end_position
                )
                extracted_sections[section.section_type.value] = content.strip()
            
            # If no sections found, try fallback extraction
            if not extracted_sections:
                extracted_sections = self._fallback_extraction(normalized_text)
            
            return extracted_sections
        
        except Exception as e:
            logger.error(f"Failed to extract resume sections: {str(e)}")
            raise ResumeParsingError(f"Section extraction failed: {str(e)}")
    
    def _normalize_text_for_parsing(self, text: str) -> str:
        """Normalize text for better section identification"""
        # Remove excessive whitespace but preserve line structure
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        # Ensure consistent line endings
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        
        return text.strip()
    
    def _identify_sections(self, text: str) -> List[ExtractedSection]:
        """Identify section boundaries in the text"""
        sections = []
        lines = text.split('\n')
        
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if not line_stripped:
                continue
            
            # Check if line matches any section pattern
            section_type, confidence = self._match_section_header(line_stripped)
            
            if section_type and confidence > 0.6:  # Confidence threshold
                # Calculate position in original text
                start_pos = sum(len(lines[j]) + 1 for j in range(i))
                
                sections.append(ExtractedSection(
                    section_type=section_type,
                    title=line_stripped,
                    content="",  # Will be filled later
                    start_position=start_pos,
                    end_position=start_pos + len(line),
                    confidence=confidence
                ))
        
        # Sort sections by position and calculate end positions
        sections.sort(key=lambda x: x.start_position)
        
        for i in range(len(sections)):
            if i < len(sections) - 1:
                sections[i].end_position = sections[i + 1].start_position
            else:
                sections[i].end_position = len(text)
        
        return sections
    
    def _match_section_header(self, line: str) -> Tuple[Optional[ResumeSection], float]:
        """Match a line against section header patterns"""
        line_lower = line.lower().strip()
        
        # Remove common formatting characters
        clean_line = re.sub(r'[:\-_=*#]+', '', line_lower).strip()
        
        best_match = None
        best_confidence = 0.0
        
        for section_type, patterns in self.section_patterns.items():
            for pattern in patterns:
                # Exact match gets highest confidence
                if clean_line == pattern.replace(r'\s+', ' '):
                    return section_type, 1.0
                
                # Regex match with confidence based on match quality
                if re.search(pattern, clean_line):
                    confidence = self._calculate_match_confidence(clean_line, pattern)
                    if confidence > best_confidence:
                        best_match = section_type
                        best_confidence = confidence
        
        return best_match, best_confidence
    
    def _calculate_match_confidence(self, line: str, pattern: str) -> float:
        """Calculate confidence score for pattern match"""
        # Base confidence for regex match
        confidence = 0.7
        
        # Boost confidence for shorter lines (likely headers)
        if len(line) < 30:
            confidence += 0.1
        
        # Boost confidence for lines that are mostly the pattern
        pattern_words = set(re.findall(r'\w+', pattern))
        line_words = set(re.findall(r'\w+', line.lower()))
        
        if pattern_words and line_words:
            overlap = len(pattern_words.intersection(line_words))
            overlap_ratio = overlap / len(pattern_words)
            confidence += overlap_ratio * 0.2
        
        return min(confidence, 1.0)
    
    def _extract_section_content(self, text: str, start_pos: int, end_pos: int) -> str:
        """Extract content between section boundaries"""
        content = text[start_pos:end_pos]
        
        # Remove the section header (first line)
        lines = content.split('\n')
        if lines:
            lines = lines[1:]  # Skip header line
        
        return '\n'.join(lines).strip()
    
    def _fallback_extraction(self, text: str) -> Dict[str, str]:
        """Fallback extraction when no clear sections are found"""
        sections = {}
        
        # Try to extract contact information from the beginning
        contact_info = self._extract_contact_info(text)
        if contact_info:
            sections[ResumeSection.CONTACT.value] = contact_info
        
        # Try to extract skills using keyword patterns
        skills = self._extract_skills_fallback(text)
        if skills:
            sections[ResumeSection.SKILLS.value] = skills
        
        # Try to extract experience using date patterns
        experience = self._extract_experience_fallback(text)
        if experience:
            sections[ResumeSection.EXPERIENCE.value] = experience
        
        # Try to extract education using degree patterns
        education = self._extract_education_fallback(text)
        if education:
            sections[ResumeSection.EDUCATION.value] = education
        
        # Put remaining text in "other" section
        if not sections:
            sections[ResumeSection.OTHER.value] = text
        
        return sections
    
    def _extract_contact_info(self, text: str) -> str:
        """Extract contact information from text"""
        # Look for email, phone, address patterns in first few lines
        lines = text.split('\n')[:10]  # Check first 10 lines
        contact_lines = []
        
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
        
        for line in lines:
            if re.search(email_pattern, line) or re.search(phone_pattern, line):
                contact_lines.append(line.strip())
            elif any(keyword in line.lower() for keyword in ['address', 'linkedin', 'github']):
                contact_lines.append(line.strip())
        
        return '\n'.join(contact_lines) if contact_lines else ""
    
    def _extract_skills_fallback(self, text: str) -> str:
        """Extract skills using keyword patterns"""
        skill_keywords = [
            'python', 'java', 'javascript', 'react', 'angular', 'vue',
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis',
            'aws', 'azure', 'docker', 'kubernetes', 'git',
            'machine learning', 'data science', 'artificial intelligence'
        ]
        
        found_skills = []
        text_lower = text.lower()
        
        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill)
        
        return ', '.join(found_skills) if found_skills else ""
    
    def _extract_experience_fallback(self, text: str) -> str:
        """Extract experience using date and job title patterns"""
        # Look for date ranges and job titles
        date_pattern = r'\b(19|20)\d{2}\b'
        lines = text.split('\n')
        
        experience_lines = []
        for line in lines:
            if re.search(date_pattern, line):
                # Check if line contains job-related keywords
                job_keywords = ['engineer', 'developer', 'manager', 'analyst', 'specialist', 'coordinator']
                if any(keyword in line.lower() for keyword in job_keywords):
                    experience_lines.append(line.strip())
        
        return '\n'.join(experience_lines) if experience_lines else ""
    
    def _extract_education_fallback(self, text: str) -> str:
        """Extract education using degree patterns"""
        degree_patterns = [
            r'\b(bachelor|master|phd|doctorate|associate)\b',
            r'\b(b\.?s\.?|m\.?s\.?|m\.?a\.?|ph\.?d\.?)\b',
            r'\b(university|college|institute)\b'
        ]
        
        lines = text.split('\n')
        education_lines = []
        
        for line in lines:
            line_lower = line.lower()
            if any(re.search(pattern, line_lower) for pattern in degree_patterns):
                education_lines.append(line.strip())
        
        return '\n'.join(education_lines) if education_lines else ""
    
    async def parse_resume(self, resume_text: str) -> ParsedResume:
        """
        Parse a resume into a structured format with sections, skills, and metadata.
        
        Args:
            resume_text: Raw resume text to parse
            
        Returns:
            ParsedResume model containing structured resume data
        
        Raises:
            ResumeParsingError: If parsing fails
        """
        if not resume_text or not resume_text.strip():
            raise ResumeParsingError("Resume text is empty or invalid")
            
        try:
            # Extract sections
            normalized_text = self._normalize_text_for_parsing(resume_text)
            sections = self._identify_sections(normalized_text)
            
            # Extract skills
            extracted_skills = await self.extract_skills_detailed(resume_text)
            skill_list = []
            for skills in extracted_skills.values():
                skill_list.extend(skills)
            
            # Calculate overall confidence
            section_confidences = [section.confidence for section in sections]
            avg_confidence = sum(section_confidences) / len(section_confidences) if section_confidences else 0.6
            
            # Build metadata
            metadata = {
                "has_contact_info": any(s.section_type == ResumeSection.CONTACT for s in sections),
                "has_experience": any(s.section_type == ResumeSection.EXPERIENCE for s in sections),
                "has_education": any(s.section_type == ResumeSection.EDUCATION for s in sections),
                "has_skills": any(s.section_type == ResumeSection.SKILLS for s in sections),
                "section_count": len(sections),
                "text_length": len(resume_text)
            }
            
            return ParsedResume(
                raw_text=resume_text,
                sections=sections,
                metadata=metadata,
                extracted_skills=skill_list,
                confidence_score=avg_confidence
            )
            
        except Exception as e:
            logger.error(f"Failed to parse resume: {str(e)}")
            raise ResumeParsingError(f"Resume parsing failed: {str(e)}")

    async def extract_skills_detailed(self, text: str) -> Dict[str, List[str]]:
        """
        Extract detailed skills categorization from resume text.
        
        Args:
            text: Resume text to analyze
            
        Returns:
            Dictionary with categorized skills
        """
        skills_categories = {
            'programming_languages': [],
            'frameworks': [],
            'databases': [],
            'tools': [],
            'soft_skills': [],
            'certifications': []
        }
        
        # Define skill patterns for each category
        skill_patterns = {
            'programming_languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'go', 'rust',
                'php', 'ruby', 'swift', 'kotlin', 'scala', 'r', 'matlab'
            ],
            'frameworks': [
                'react', 'angular', 'vue', 'django', 'flask', 'spring', 'express',
                'laravel', 'rails', 'tensorflow', 'pytorch', 'scikit-learn'
            ],
            'databases': [
                'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch',
                'oracle', 'sql server', 'sqlite', 'cassandra', 'dynamodb'
            ],
            'tools': [
                'git', 'docker', 'kubernetes', 'jenkins', 'aws', 'azure', 'gcp',
                'terraform', 'ansible', 'jira', 'confluence', 'slack'
            ],
            'soft_skills': [
                'leadership', 'communication', 'teamwork', 'problem solving',
                'project management', 'agile', 'scrum', 'mentoring'
            ]
        }
        
        text_lower = text.lower()
        
        for category, skills in skill_patterns.items():
            for skill in skills:
                if skill in text_lower:
                    skills_categories[category].append(skill)
        
        return skills_categories
    
    def validate_extracted_sections(self, sections: Dict[str, str]) -> Dict[str, bool]:
        """
        Validate the quality of extracted sections.
        
        Args:
            sections: Dictionary of extracted sections
            
        Returns:
            Dictionary indicating validation status for each section
        """
        validation_results = {}
        
        for section_name, content in sections.items():
            is_valid = True
            
            # Check minimum content length
            if len(content.strip()) < 10:
                is_valid = False
            
            # Section-specific validation
            if section_name == ResumeSection.CONTACT.value:
                # Should contain email or phone
                email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                phone_pattern = r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})'
                if not (re.search(email_pattern, content) or re.search(phone_pattern, content)):
                    is_valid = False
            
            elif section_name == ResumeSection.EXPERIENCE.value:
                # Should contain dates or job titles
                date_pattern = r'\b(19|20)\d{2}\b'
                if not re.search(date_pattern, content):
                    is_valid = False
            
            elif section_name == ResumeSection.EDUCATION.value:
                # Should contain degree or institution keywords
                edu_keywords = ['university', 'college', 'degree', 'bachelor', 'master', 'phd']
                if not any(keyword in content.lower() for keyword in edu_keywords):
                    is_valid = False
            
            validation_results[section_name] = is_valid
        
        return validation_results


# Global resume parser instance
resume_parser = ResumeParser()