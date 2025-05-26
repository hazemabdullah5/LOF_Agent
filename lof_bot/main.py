from pathlib import Path
import sys
import io
from contextlib import redirect_stdout

from agno.agent import Agent
from agno.knowledge.csv import CSVKnowledgeBase
from agno.vectordb.pgvector import PgVector

# Import the FAQCacheMemory from memory.py
from memory import FAQCacheMemory

# Try to import custom modules, with fallback if they don't exist
try:
    from system_prompts import SystemPrompt
    from fallback_handler import FallbackHandler
    MODULES_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import custom modules: {e}")
    print("Running with basic functionality...")
    MODULES_AVAILABLE = False
    
    # Define minimal fallback classes
    class SystemPrompt:
        def get_full_system_prompt(self):
            return "You are a helpful assistant for Lab of Future. Provide short, direct answers about courses, company, and services."
        def get_greeting_message(self):
            return "Hello! I'm your Lab of Future learning assistant. How can I help you today?"
        def get_error_message(self):
            return "Sorry, I'm having trouble right now. Please try again."
    
    class FallbackHandler:
        def __init__(self, similarity_threshold=0.7):
            pass
        def is_educational_query(self, query):
            return True
        def process_response(self, response, query):
            return response, False
        def enhance_response(self, response, query):
            return response

# Database configuration
db_url = "postgresql+psycopg://postgres:12345@localhost:5433/ai"

# Initialize system components
system_prompt = SystemPrompt()
fallback_handler = FallbackHandler(similarity_threshold=0.7)

# Initialize knowledge base
knowledge_base = CSVKnowledgeBase(
    path=Path(r"C:\Users\TRG-LOF-131-048\Desktop\LOF_BOT\laboffuture_chunks.csv"),
    vector_db=PgVector(
        table_name="csv_documents",
        db_url=db_url,
    ),
    num_documents=5,  # Number of chunks to return on search
)

# Load or recreate the knowledge base index
knowledge_base.load(recreate=False)

# Initialize the Agent with the knowledge base and system prompt
agent = Agent(
    knowledge=knowledge_base,
    search_knowledge=True,
    instructions=system_prompt.get_full_system_prompt(),  # Add system prompt here
)

# Initialize FAQ cache memory
faq_cache = FAQCacheMemory(db_url=db_url)

def get_agent_response(query: str) -> str:
    """
    Capture agent response as string instead of printing directly
    """
    output_buffer = io.StringIO()
    
    try:
        with redirect_stdout(output_buffer):
            agent.print_response(query, markdown=True)
        response = output_buffer.getvalue().strip()
        return response
    except Exception as e:
        print(f"Error getting agent response: {e}")
        return ""

def process_user_query(user_query: str) -> str:
    """
    Process user query through the complete pipeline with FAQ cache:
    1. Check FAQ cache for cached answer
    2. If no cache hit, check if query in scope
    3. Get agent response if appropriate
    4. Apply fallback handling
    5. Enhance final response
    6. Cache the new response for future
    """
    
    # 1. Check FAQ cache memory first
    cached = faq_cache.get_cached_response(user_query)
    if cached:
        return cached

    # 2. If not cached, check if the query is within our educational scope
    if not fallback_handler.is_educational_query(user_query):
        return fallback_handler.get_fallback_response(user_query)

    # 3. Get response from the agent
    agent_response = get_agent_response(user_query)
    
    # 4. Process the response through fallback handler
    processed_response, used_fallback = fallback_handler.process_response(agent_response, user_query)
    
    # 5. Enhance the response with company context
    final_response = fallback_handler.enhance_response(processed_response, user_query)
    
    # 6. Cache the final response for future queries
    faq_cache.cache_response(user_query, final_response)
    
    return final_response

def main():
    """Main chatbot loop"""
    print("=" * 60)
    print("🎓 Lab of Future Learning Assistant")
    print("=" * 60)
    print(system_prompt.get_greeting_message())
    print("\nType 'exit', 'quit', or 'bye' to end the conversation.")
    print("-" * 60)
    
    while True:
        try:
            user_query = input("\n🧑 You: ").strip()
            
            if user_query.lower() in ["exit", "quit", "bye", "goodbye"]:
                print("\n🤖 Lab of Future Assistant: Thank you for using our learning assistant! Goodbye! 👋")
                break
            
            if not user_query:
                print("\n🤖 Lab of Future Assistant: I'm here to help! Please ask me anything about our courses or company.")
                continue
            
            print("\n🤖 Lab of Future Assistant: ", end="")
            response = process_user_query(user_query)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\n🤖 Lab of Future Assistant: Goodbye! Have a great day! 👋")
            break
        except Exception as e:
            print(f"\n🤖 Lab of Future Assistant: {system_prompt.get_error_message()}")
            print(f"Debug info: {str(e)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Failed to start chatbot: {e}")
        print("Please check your database connection and file paths.")
        sys.exit(1)
