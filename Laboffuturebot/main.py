"""
Main module for Lab o Future chatbot.
Integrates knowledge base, fallback handling, and system prompts.
"""
import io
import sys
from typing import Dict, Any, Optional

from agno.agent import Agent

from knowledge_base import create_knowledge_base
from fallback_handler import create_fallback_handler
from system_prompts import get_system_prompts
from utils import load_config, log_conversation, get_performance_monitor


class LabOFutureChatbot:
    """
    Main chatbot class that integrates all components.
    """
    
    def __init__(self, config_path: str = "config.json"):
        """
        Initialize the chatbot with all required components.
        
        Args:
            config_path: Path to configuration file
        """
        # Load configuration
        self.config = load_config(config_path)
        
        # Initialize components
        self.perf_monitor = get_performance_monitor()
        self.system_prompts = get_system_prompts()
        
        # Initialize knowledge base
        self.perf_monitor.start("init_knowledge_base")
        self.kb = create_knowledge_base(
            csv_path=self.config["csv_path"],
            db_url=self.config["db_url"],
            similarity_threshold=self.config["similarity_threshold"]
        )
        self.perf_monitor.stop()
        
        # Initialize fallback handler
        self.fallback_handler = create_fallback_handler(education_focused=True)
        
        # Initialize agent with default persona
        self.current_persona = self.config["default_persona"]
        self._init_agent()
        
        # Conversation history
        self.conversation_history = []
        
    def _init_agent(self):
        """Initialize or reinitialize the agent with current settings."""
        # Initialize Agno agent (without system prompt as it doesn't support it directly)
        self.agent = Agent(
            knowledge=self.kb.knowledge_base,
            search_knowledge=True,
        )
        
        # Store current system prompt for use in response generation
        self.current_system_prompt = self.system_prompts.get_prompt(self.current_persona)
    
    def set_persona(self, persona_key: str) -> bool:
        """
        Set the chatbot persona.
        
        Args:
            persona_key: Key identifying which persona to use
            
        Returns:
            Success status
        """
        if persona_key not in self.system_prompts.personas:
            return False
            
        self.current_persona = persona_key
        self._init_agent()
        return True
    
    def get_response(self, query: str) -> Dict[str, Any]:
        """
        Get a response from the chatbot for a user query.
        
        Args:
            query: User's query text
            
        Returns:
            Response dictionary with text and metadata
        """
        self.perf_monitor.start("query_processing")
        
        # Direct interaction with the underlying knowledge base to get documents
        self.perf_monitor.start("knowledge_search")
        # Use the vector_db directly since we can't use kb.query
        documents = self.kb.knowledge_base.query(query)
        
        # Extract results and check relevance
        kb_results = []
        is_relevant = False
        max_score = 0
        
        for doc in documents:
            # Extract content and metadata based on what's available
            content = getattr(doc, 'page_content', None)
            if content is None and hasattr(doc, 'get'):
                content = doc.get('content', '')
                
            # Extract score from metadata if available
            score = 0
            if hasattr(doc, 'metadata'):
                score = doc.metadata.get('score', 0)
            elif hasattr(doc, 'get'):
                score = doc.get('score', 0)
                
            kb_results.append({
                'content': content,
                'score': score
            })
            
            # Update maximum score and relevance
            if score > max_score:
                max_score = score
                
            if score >= self.kb.similarity_threshold:
                is_relevant = True
                
        self.perf_monitor.stop()  # Stop knowledge_search timer
        
        # Prepare the response structure
        response = {
            "text": "",
            "source": "knowledge_base" if is_relevant else "fallback",
            "persona": self.current_persona,
            "metadata": {
                "query_time": 0,
                "sources": [item['content'][:100] + "..." for item in kb_results if item['content']],
                "confidence": max_score
            }
        }
        
        # Generate the response text
        if is_relevant:
            # Since Agent.print_response prints to stdout, we need to capture it
            self.perf_monitor.start("agent_response")
            
            # Capture stdout to get agent's response
            original_stdout = sys.stdout
            captured_output = io.StringIO()
            sys.stdout = captured_output
            
            # Use the agent to generate a response (it prints instead of returning)
            # We could inject the system prompt here if supported
            self.agent.print_response(query, markdown=True)
            
            # Restore stdout and get the captured output
            sys.stdout = original_stdout
            agent_response = captured_output.getvalue()
            
            self.perf_monitor.stop()  # Stop agent_response timer
            
            response["text"] = agent_response
        else:
            # Use fallback handler if no relevant information found
            fallback_response = self.fallback_handler.get_fallback_response(query)
            response["text"] = fallback_response["text"]
            response["metadata"]["suggestions"] = fallback_response.get("suggestions", [])
        
        # Record the conversation
        self.conversation_history.append({
            "user": query,
            "bot": response["text"]
        })
        
        # Log the conversation if enabled
        if self.config.get("log_conversations", False):
            log_conversation(
                user_query=query,
                bot_response=response["text"],
                metadata={
                    "source": response["source"],
                    "persona": self.current_persona,
                    "confidence": response["metadata"].get("confidence", 0)
                },
                log_dir=self.config.get("log_path", "conversation_logs")
            )
        
        query_time = self.perf_monitor.stop()  # Stop query_processing timer
        response["metadata"]["query_time"] = query_time
        
        return response
    
    def get_available_personas(self):
        """Get list of available personas."""
        return self.system_prompts.list_personas()
    
    def get_performance_stats(self):
        """Get performance statistics."""
        return self.perf_monitor.get_stats()
    
    def update_knowledge_base(self, recreate: bool = True):
        """
        Update the knowledge base index.
        
        Args:
            recreate: Whether to recreate the index
        """
        self.perf_monitor.start("update_kb")
        self.kb.update_index(recreate=recreate)
        self.perf_monitor.stop()


# Factory function for easy instantiation
def create_chatbot(config_path: str = "config.json") -> LabOFutureChatbot:
    """
    Create a chatbot instance.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Initialized LabOFutureChatbot
    """
    return LabOFutureChatbot(config_path=config_path)


if __name__ == "__main__":
    # Basic CLI for testing/demonstration
    chatbot = create_chatbot()
    print("Lab o Future Chatbot initialized")
    print(f"Using persona: {chatbot.current_persona}")
    print("\nAvailable personas:")
    for persona in chatbot.get_available_personas():
        print(f"- {persona['name']}: {persona['description']}")
    
    print("\nChatbot ready! Type 'exit' to quit, 'persona:NAME' to change persona")
    
    while True:
        user_input = input("\nYou: ")
        
        if user_input.lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
            
        # Check for persona change command
        if user_input.lower().startswith("persona:"):
            persona_key = user_input.split(":", 1)[1].strip()
            if chatbot.set_persona(persona_key):
                print(f"Switched to persona: {persona_key}")
            else:
                print(f"Unknown persona: {persona_key}")
            continue
            
        # Get and display response
        response = chatbot.get_response(user_input)
        print(f"\nBot ({response['source']}): {response['text']}")
        
        # Show confidence if available
        confidence = response["metadata"].get("confidence", 0)
        if confidence > 0:
            print(f"Confidence: {confidence:.2f}")