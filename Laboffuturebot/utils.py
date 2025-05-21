"""
Utility functions for the Lab o Future chatbot.
"""
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration and settings management
def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """
    Load configuration from a JSON file.
    
    Args:
        config_path: Path to the configuration file
        
    Returns:
        Configuration dictionary
    """
    default_config = {
        "db_url": "postgresql+psycopg://postgres:12345@localhost:5433/ai",
        "csv_path": "laboffuture_chunks.csv",
        "similarity_threshold": 0.7,
        "default_persona": "default",
        "log_conversations": True,
        "log_path": "conversation_logs"
    }
    
    if not os.path.exists(config_path):
        # Create default config if it doesn't exist
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        return default_config
    
    try:
        with open(config_path, 'r') as f:
            config = json.load(f)
            # Merge with defaults for any missing keys
            for key, value in default_config.items():
                if key not in config:
                    config[key] = value
            return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return default_config

# Conversation logging
def log_conversation(
    user_query: str, 
    bot_response: str, 
    metadata: Optional[Dict[str, Any]] = None,
    log_dir: str = "conversation_logs"
) -> None:
    """
    Log conversation to a file.
    
    Args:
        user_query: User's query text
        bot_response: Bot's response text
        metadata: Additional metadata about the conversation
        log_dir: Directory to store logs
    """
    # Create log directory if it doesn't exist
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Create log entry
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "user_query": user_query,
        "bot_response": bot_response
    }
    
    if metadata:
        log_entry["metadata"] = metadata
    
    # Write to daily log file
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"conversation_log_{today}.jsonl")
    
    with open(log_file, 'a') as f:
        f.write(json.dumps(log_entry) + "\n")

# Performance monitoring
class PerformanceMonitor:
    """Simple performance monitoring utility."""
    
    def __init__(self):
        self.start_time = None
        self.metrics = {}
    
    def start(self, operation: str) -> None:
        """Start timing an operation."""
        self.start_time = time.time()
        self.current_operation = operation
    
    def stop(self) -> float:
        """
        Stop timing the current operation.
        
        Returns:
            Duration in seconds
        """
        if self.start_time is None:
            return 0
            
        duration = time.time() - self.start_time
        
        if self.current_operation not in self.metrics:
            self.metrics[self.current_operation] = []
            
        self.metrics[self.current_operation].append(duration)
        self.start_time = None
        
        return duration
    
    def get_stats(self) -> Dict[str, Dict[str, float]]:
        """
        Get statistics about measured operations.
        
        Returns:
            Dictionary with operation statistics
        """
        stats = {}
        
        for op, durations in self.metrics.items():
            if not durations:
                continue
                
            stats[op] = {
                "avg": sum(durations) / len(durations),
                "min": min(durations),
                "max": max(durations),
                "count": len(durations),
                "total": sum(durations)
            }
            
        return stats

# Text processing utilities
def extract_keywords(text: str, max_keywords: int = 5) -> List[str]:
    """
    Extract key words/phrases from text using a simple approach.
    
    Args:
        text: Input text
        max_keywords: Maximum number of keywords to extract
        
    Returns:
        List of extracted keywords
    """
    # A very simple implementation - in production, consider using a proper NLP library
    # This is just a placeholder
    common_words = {"the", "and", "is", "in", "to", "of", "a", "for", "on", "with"}
    words = text.lower().split()
    
    # Remove common words and short words
    filtered = [word for word in words if word not in common_words and len(word) > 3]
    
    # Count occurrences
    word_counts = {}
    for word in filtered:
        word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by count and return top words
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    return [word for word, count in sorted_words[:max_keywords]]


# Create a performance monitor instance
performance_monitor = PerformanceMonitor()

def get_performance_monitor() -> PerformanceMonitor:
    """Get the performance monitor singleton instance."""
    return performance_monitor
