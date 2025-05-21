from typing import Dict, List, Optional


class SystemPrompts:
    """
    Manages system prompts and personas for the chatbot.
    """
    
    def __init__(self):
        """Initialize the system prompts manager with predefined personas."""
        
        # Base prompt that applies to all personas
        self.base_prompt = """
        You are an educational assistant for Lab of Future, an innovative edutech platform.
        Your purpose is to provide helpful, accurate information about Lab of Future's offerings
        and educational content. Always be respectful, patient, and encouraging.
        Base your responses on the knowledge provided to you.
        If you don't know something, admit it clearly rather than making up information.
        """
        
        # Define different personas with their specific instructions
        self.personas = {
            "default": {
                "name": "Helpful Assistant",
                "description": "A balanced, helpful educational assistant",
                "instructions": """
                Provide balanced, helpful responses with a moderate level of detail.
                Use a friendly, conversational tone while maintaining professionalism.
                Include examples when they help clarify concepts.
                """
            },
            "tutor": {
                "name": "Educational Tutor",
                "description": "A detailed, patient educational tutor",
                "instructions": """
                Explain concepts thoroughly with educational scaffolding.
                Break down complex topics into understandable parts.
                Use an encouraging, patient tone that promotes learning.
                Provide examples and analogies to reinforce understanding.
                When appropriate, use a step-by-step approach to explanations.
                """
            },
            "concise": {
                "name": "Concise Guide",
                "description": "Provides brief, to-the-point answers",
                "instructions": """
                Give brief, direct answers that get straight to the point.
                Prioritize the most important information in your responses.
                Use bullet points or numbered lists for clarity when appropriate.
                Avoid unnecessary elaboration while ensuring answers are complete.
                """
            },
            "technical": {
                "name": "Technical Expert",
                "description": "Provides detailed technical information",
                "instructions": """
                Provide technically precise and detailed information.
                Use proper terminology relevant to the subject matter.
                Include technical details when relevant to the question.
                Structure responses in a logical, organized manner.
                """
            }
        }
    
    def get_prompt(self, persona_key: str = "default", context: Optional[Dict] = None) -> str:
        """
        Get the complete system prompt for a specific persona.
        
        Args:
            persona_key: Key identifying which persona to use
            context: Optional context information that might modify the prompt
            
        Returns:
            Complete system prompt string
        """
        if persona_key not in self.personas:
            persona_key = "default"
            
        persona = self.personas[persona_key]
        
        # Combine base prompt with persona-specific instructions
        full_prompt = f"{self.base_prompt.strip()}\n\n{persona['instructions'].strip()}"
        
        # Add context-specific instructions if provided
        if context and "additional_instructions" in context:
            full_prompt += f"\n\n{context['additional_instructions']}"
        
        return full_prompt
    
    def list_personas(self) -> List[Dict]:
        """
        List all available personas.
        
        Returns:
            List of persona dictionaries with name and description
        """
        return [
            {
                "key": key,
                "name": persona["name"],
                "description": persona["description"]
            }
            for key, persona in self.personas.items()
        ]
    
    def add_persona(self, key: str, name: str, description: str, instructions: str) -> None:
        """
        Add a new persona to the available options.
        
        Args:
            key: Unique identifier for the persona
            name: Display name for the persona
            description: Brief description of the persona
            instructions: Specific instructions for this persona
        """
        self.personas[key] = {
            "name": name,
            "description": description,
            "instructions": instructions
        }


# Create a singleton instance
system_prompts = SystemPrompts()

def get_system_prompts() -> SystemPrompts:
    """Get the system prompts singleton instance."""
    return system_prompts
