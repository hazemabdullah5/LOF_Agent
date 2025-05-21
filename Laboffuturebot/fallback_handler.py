from typing import Dict, Optional, List, Any


class FallbackHandler:
    """
    Handles fallback responses when the knowledge base doesn't contain relevant information.
    """
    
    def __init__(self, education_focused: bool = True):
        """
        Initialize the fallback handler.
        
        Args:
            education_focused: Whether to use education-focused fallback responses
        """
        self.education_focused = education_focused
        
        # Predefined fallback responses by category
        self.general_fallbacks = [
            "I don't have specific information about that in my knowledge base. Could you try rephrasing your question?",
            "I'm not finding relevant information about this topic. Is there something else related to Lab of Future I can help with?",
            "That's outside my current knowledge base. Could you ask something about Lab of Future's educational offerings?"
        ]
        
        self.edu_fallbacks = [
            "I don't have that specific information in my knowledge base yet. To learn more about this topic, you might want to check the Lab of Future learning resources.",
            "This appears to be beyond my current educational content. Would you like me to suggest some related topics I can help with?",
            "I don't have detailed information on that specific topic. For the best learning experience, consider checking Lab of Future's course catalog for related subjects."
        ]
        
        # Topic suggestions when user might be going off-topic
        self.topic_suggestions = {
            "courses": ["available courses", "course structure", "enrollment", "prerequisites"],
            "technology": ["platforms used", "technical requirements", "tools", "software"],
            "assessments": ["grading", "assignments", "projects", "evaluation"],
            "support": ["tutoring", "help services", "contact information"]
        }
    
    def get_fallback_response(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate a fallback response when knowledge base doesn't have an answer.
        
        Args:
            query: The user's query text
            context: Optional context information about the conversation
            
        Returns:
            Dictionary containing response text and metadata
        """
        # Determine the most appropriate fallback response
        if self.education_focused:
            fallback_base = self.edu_fallbacks
        else:
            fallback_base = self.general_fallbacks
        
        # Use context to select the most appropriate response (can be enhanced)
        import random
        response_text = random.choice(fallback_base)
        
        # Try to suggest related topics
        suggestions = self._get_topic_suggestions(query)
        
        if suggestions:
            response_text += f"\n\nYou might be interested in these topics: {', '.join(suggestions)}."
        
        return {
            "text": response_text,
            "source": "fallback",
            "confidence": 0.0,
            "suggestions": suggestions
        }
    
    def _get_topic_suggestions(self, query: str) -> List[str]:
        """
        Get topic suggestions based on the query.
        
        Args:
            query: The user's query text
            
        Returns:
            List of suggested topics
        """
        # Simple keyword matching - could be enhanced with embeddings
        query_lower = query.lower()
        
        # Check each category for keyword matches
        for category, topics in self.topic_suggestions.items():
            if category in query_lower or any(word in query_lower for word in topics):
                return topics
        
        # If no specific match, return a mix of topics
        import random
        all_topics = [topic for sublist in self.topic_suggestions.values() for topic in sublist]
        return random.sample(all_topics, min(3, len(all_topics)))


# Factory function to create a fallback handler
def create_fallback_handler(education_focused: bool = True) -> FallbackHandler:
    """
    Create a fallback handler instance.
    
    Args:
        education_focused: Whether to use education-focused fallback responses
        
    Returns:
        Initialized FallbackHandler
    """
    return FallbackHandler(education_focused=education_focused)