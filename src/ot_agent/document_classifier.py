"""
Document classifier module for OT Local Agent.
Provides AI-based classification of uploaded documents into types and categories.
"""

import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


# Document type patterns (Russian regulatory documents)
DOCUMENT_TYPE_PATTERNS = {
    # Safety instructions
    "INSTRUCTION": [
        r"\b\u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044f\b",
        r"\b\u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044f\b",
        r"\b\u0438\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u043e\u043d\u043d\u0430\u044f\b",
    ],
    # Orders
    "ORDER": [
        r"\b\u043f\u0440\u0438\u043a\u0430\u0437\b",
        r"\b\u043f\u0440\u0438\u043a\u0430\u0437\u043e\u043c\b",
    ],
    # Regulations
    "REGULATION": [
        r"\b\u043f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u0435\b",
        r"\b\u043f\u0440\u0430\u0432\u0438\u043b\u0430\b",
    ],
    # Standards
    "STANDARD": [
        r"\b\u0413\u041e\u0421\u0422\b",
        r"\b\u0421\u0422\u041e\b",
        r"\b\u041c\u0435\u0436\u0433\u043e\u0441\u0443\u0434\u0430\u0440\u0441\u0442\u0432\u0435\u043d\u043d\u044b\u0439\b",
    ],
    # Technical documentation
    "TECHNICAL_DOC": [
        r"\b\u0442\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0430\u044f\b",
        r"\b\u0442\u0435\u0445\u043f\u0430\u0441\u043f\u043e\u0440\u0442\b",
    ],
    # Safety data sheets
    "SAFETY_DATA_SHEET": [
        r"\b\u043f\u0430\u0441\u043f\u043e\u0440\u0442\b",
        r"\b\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c\b",
    ],
    # Acts
    "ACT": [
        r"\b\u0430\u043a\u0442\b",
        r"\b\u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\b",
    ],
    # Journals/Logs
    "JOURNAL": [
        r"\b\u0436\u0443\u0440\u043d\u0430\u043b\b",
        r"\b\u0440\u0435\u0435\u0441\u0442\u0440\b",
    ],
    # Plans
    "PLAN": [
        r"\b\u043f\u043b\u0430\u043d\b",
        r"\b\u043f\u043b\u0430\u043d\u043e\u0432\u044b\u0439\b",
    ],
}

# Document category patterns
DOCUMENT_CATEGORY_PATTERNS = {
    "FIRE_SAFETY": [
        r"\b\u043f\u043e\u0436\u0430\u0440\u043d\u0430\u044f\b",
        r"\b\u043e\u0433\u043d\u0435\u0442\u0443\u0448\u0438\u0442\u0435\u043b\u044c\u043d\u044b\u0439\b",
        r"\b\u043f\u043e\u0436\u0430\u0440\u043d\u044b\u0439\b",
    ],
    "ELECTRICAL_SAFETY": [
        r"\b\u044d\u043b\u0435\u043a\u0442\u0440\u043e\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c\b",
        r"\b\u044d\u043b\u0435\u043a\u0442\u0440\u043e\u0442\u0435\u0445\u043d\u0438\u043a\u0430\b",
    ],
    "INDUSTRIAL_SAFETY": [
        r"\b\u043f\u0440\u043e\u043c\u044b\u0448\u043b\u0435\u043d\u043d\u0430\u044f\b",
        r"\b\u043f\u0440\u043e\u043c\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c\b",
    ],
    "OCCUPATIONAL_SAFETY": [
        r"\b\u043e\u0445\u0440\u0430\u043d\u0430\b",
        r"\b\u0442\u0440\u0443\u0434\u0430\b",
        r"\b\u043e\u0442\b",
    ],
    "ENVIRONMENTAL": [
        r"\b\u044d\u043a\u043e\u043b\u043e\u0433\u0438\u044f\b",
        r"\b\u043e\u043a\u0440\u0443\u0436\u0430\u044e\u0449\u0430\u044f\b",
    ],
    "HEALTH_SAFETY": [
        r"\b\u0437\u0434\u0440\u0430\u0432\u043e\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435\b",
        r"\b\u043c\u0435\u0434\u0438\u0446\u0438\u043d\u0430\b",
    ],
}

# Topic classification
TOPIC_PATTERNS = {
    "OT": [
        r"\b\u043e\u0445\u0440\u0430\u043d\u0430\b",
        r"\b\u0442\u0440\u0443\u0434\u0430\b",
        r"\b\u043e\u0442\b",
    ],
    "FIRE": [
        r"\b\u043f\u043e\u0436\u0430\u0440\u043d\u0430\u044f\b",
        r"\b\u043f\u043e\u0436\u0430\u0440\u043d\u044b\u0439\b",
    ],
    "GO_CHS": [
        r"\b\u0413\u043e\u0441\u0442\u0440\u043e\u0434\b",
        r"\b\u0413\u0440\u0430\u0436\u0434\u0430\u043d\u0441\u043a\u0430\u044f\b",
    ],
    "INDUSTRIAL_SAFETY": [
        r"\b\u043f\u0440\u043e\u043c\u044b\u0448\u043b\u0435\u043d\u043d\u0430\u044f\b",
        r"\b\u043f\u0440\u043e\u043c\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c\b",
    ],
    "ECOLOGY": [
        r"\b\u044d\u043a\u043e\u043b\u043e\u0433\u0438\u044f\b",
    ],
}

# Predefined document types
DOCUMENT_TYPES = {
    "INSTRUCTION": {"code": "INSTR", "title": "\u0418\u043d\u0441\u0442\u0440\u0443\u043a\u0446\u0438\u044f", "topic": "OT"},
    "ORDER": {"code": "ORD", "title": "\u041f\u0440\u0438\u043a\u0430\u0437", "topic": "OT"},
    "REGULATION": {"code": "REG", "title": "\u041f\u043e\u043b\u043e\u0436\u0435\u043d\u0438\u0435", "topic": "OT"},
    "STANDARD": {"code": "STD", "title": "\u0421\u0442\u0430\u043d\u0434\u0430\u0440\u0442", "topic": "OT"},
    "ACT": {"code": "ACT", "title": "\u0410\u043a\u0442", "topic": "OT"},
    "JOURNAL": {"code": "JRN", "title": "\u0416\u0443\u0440\u043d\u0430\u043b", "topic": "OT"},
    "PLAN": {"code": "PLN", "title": "\u041f\u043b\u0430\u043d", "topic": "OT"},
    "TECHNICAL_DOC": {"code": "TECH", "title": "\u0422\u0435\u0445\u043d\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u0430\u0446\u0438\u044f", "topic": "OT"},
    "SAFETY_DATA_SHEET": {"code": "SDS", "title": "\u041f\u0430\u0441\u043f\u043e\u0440\u0442 \u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u0438", "topic": "OT"},
}

# Predefined categories
DOCUMENT_CATEGORIES = {
    "FIRE_SAFETY": "\u041f\u043e\u0436\u0430\u0440\u043d\u0430\u044f \u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c",
    "ELECTRICAL_SAFETY": "\u042d\u043b\u0435\u043a\u0444\u0440\u043e\u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043e\u0441\u0442\u044c",
    "INDUSTRIAL_SAFETY": "\u041f\u0440\u043e\u043c\u044b\u0448\u043b\u0435\u043d\u043d\u0430\u044f \u0431\u0435\u0437\u043e\u043f\u0430\u0441\u043d\u043f\u0441\u0442\u044c",
    "OCCUPATIONAL_SAFETY": "\u041e\u0445\u0440\u0430\u043d\u0430 \u0442\u0440\u0443\u0434\u0430",
    "ENVIRONMENTAL": "\u042d\u043a\u043e\u043b\u043e\u0433\u0438\u044f",
    "HEALTH_SAFETY": "\u041e\u0445\u0440\u0430\u043d\u0430 \u0437\u0434\u043e\u0440\u043e\u0432\u044c\u044f",
    "GENERAL": "\u041e\u0431\u0449\u0438\u0435 \u0434\u043e\u043a\u0443\u043c\u0435\u043d\u0442\u044b",
}


def classify_document_type(text: str) -> Tuple[str, float]:
    """
    Classify document text into a type using pattern matching.
    Returns (type_code, confidence_score)
    """
    text_lower = text.lower()
    
    for doc_type, patterns in DOCUMENT_TYPE_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return doc_type, 0.9
    
    # Fallback: use most common type
    return "INSTRUCTION", 0.5


def classify_document_category(text: str) -> Tuple[str, float]:
    """
    Classify document text into a category using pattern matching.
    Returns (category_code, confidence_score)
    """
    text_lower = text.lower()
    
    for category, patterns in DOCUMENT_CATEGORY_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return category, 0.9
    
    # Fallback: use most common category
    return "OCCUPATIONAL_SAFETY", 0.5


def classify_topic(text: str) -> Tuple[str, float]:
    """
    Classify document text into a topic using pattern matching.
    Returns (topic_code, confidence_score)
    """
    text_lower = text.lower()
    
    for topic, patterns in TOPIC_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, text_lower, re.IGNORECASE):
                return topic, 0.9
    
    # Fallback: use OT as default
    return "OT", 0.5


def extract_document_code(text: str) -> Optional[str]:
    """
    Try to extract document code from text.
    """
    # Look for patterns like "IN-001", "Приказ №123", etc.
    patterns = [
        r'[А-ЯA-Z]{2,4}-\d{2,5}',  # IN-001, PR-123
        r'\u041f\u0440\u0438\u043a\u0430\u0437\s*[N№]?\s*\d+',  # Приказ №123
        r'[А-ЯA-Z]\d{3,5}',  # A123, B456
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    
    return None


def extract_document_title(text: str, max_length: int = 200) -> str:
    """
    Extract a clean title from document text.
    """
    # Remove extra whitespace and newlines
    text = re.sub(r'\s+', ' ', text).strip()
    
    # If text is very long, take first sentence or first max_length characters
    if len(text) > max_length:
        # Try to find first sentence
        sentences = re.split(r'[.!?]', text)
        if sentences and len(sentences[0]) > 20:
            return sentences[0][:max_length]
        return text[:max_length]
    
    return text


def classify_document(text: str, filename: Optional[str] = None) -> Dict[str, any]:
    """
    Full document classification.
    Returns a dictionary with:
    - type: document type code
    - type_title: document type title
    - category: document category
    - topic: document topic
    - code: extracted document code (if any)
    - title: extracted/suggested title
    - confidence: overall confidence score
    - suggestions: list of alternative classifications
    """
    # Classify type
    doc_type, type_confidence = classify_document_type(text)
    
    # Classify category
    category, category_confidence = classify_document_category(text)
    
    # Classify topic
    topic, topic_confidence = classify_topic(text)
    
    # Extract code
    code = extract_document_code(text) or f"AUTO-{abs(hash(text)) % 10000:04d}"
    
    # Extract title
    title = extract_document_title(text)
    
    # Calculate overall confidence
    confidence = (type_confidence + category_confidence + topic_confidence) / 3
    
    # Get type info
    type_info = DOCUMENT_TYPES.get(doc_type, {"code": doc_type, "title": doc_type, "topic": topic})
    
    # Get category title
    category_title = DOCUMENT_CATEGORIES.get(category, category)
    
    return {
        "type": doc_type,
        "type_code": type_info.get("code", doc_type),
        "type_title": type_info.get("title", doc_type),
        "category": category,
        "category_title": category_title,
        "topic": topic,
        "code": code,
        "title": title,
        "confidence": round(confidence, 2),
        "suggestions": [
            {"type": dt, "title": DOCUMENT_TYPES.get(dt, {}).get("title", dt)}
            for dt in DOCUMENT_TYPES.keys()
            if dt != doc_type
        ][:3],  # Top 3 alternative types
    }


def get_all_document_types() -> List[Dict[str, str]]:
    """Get list of all available document types."""
    return [
        {"code": info["code"], "title": info["title"], "topic": info["topic"]}
        for info in DOCUMENT_TYPES.values()
    ]


def get_all_document_categories() -> List[Dict[str, str]]:
    """Get list of all available document categories."""
    return [
        {"code": code, "title": title}
        for code, title in DOCUMENT_CATEGORIES.items()
    ]
