"""
Streamlit web interface for Lab o Future chatbot.
"""
import os
import streamlit as st
import time

from main import create_chatbot


def initialize_session_state():
    """Initialize session state variables."""
    if "chatbot" not in st.session_state:
        st.session_state.chatbot = create_chatbot()
        
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if "current_persona" not in st.session_state:
        st.session_state.current_persona = st.session_state.chatbot.current_persona


def display_chat_messages():
    """Display chat message history."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            
            # Display metadata for assistant messages if available
            if message["role"] == "assistant" and "metadata" in message:
                with st.expander("Response Details"):
                    metadata = message["metadata"]
                    st.markdown(f"**Source**: {metadata.get('source', 'Unknown')}")
                    st.markdown(f"**Response Time**: {metadata.get('query_time', 0):.2f} seconds")
                    
                    # Show confidence if available
                    if "confidence" in metadata and metadata["confidence"] > 0:
                        confidence = metadata["confidence"]
                        st.progress(min(confidence, 1.0))
                        st.markdown(f"**Confidence**: {confidence:.2f}")
                    
                    # Show suggestions if available
                    if "suggestions" in metadata and metadata["suggestions"]:
                        st.markdown("**Related Topics**:")
                        for suggestion in metadata["suggestions"]:
                            st.markdown(f"- {suggestion}")


def change_persona():
    """Handle persona change from the sidebar."""
    new_persona = st.session_state.persona_selector
    if new_persona != st.session_state.current_persona:
        if st.session_state.chatbot.set_persona(new_persona):
            st.session_state.current_persona = new_persona
            
            # Add system message indicating persona change
            persona_info = next((p for p in st.session_state.chatbot.get_available_personas() 
                              if p["key"] == new_persona), None)
            
            if persona_info:
                st.session_state.messages.append({
                    "role": "system",
                    "content": f"*Switched to {persona_info['name']}*: {persona_info['description']}"
                })


def main():
    """Main Streamlit application."""
    st.set_page_config(
        page_title="Lab o Future Assistant",
        page_icon="🎓",
        layout="wide"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("Lab o Future Assistant")
        st.markdown("Your educational AI assistant")
        
        # Persona selector
        personas = st.session_state.chatbot.get_available_personas()
        persona_options = {p["name"]: p["key"] for p in personas}
        
        st.selectbox(
            "Select Assistant Persona:",
            options=list(persona_options.keys()),
            key="persona_selector_display",
            on_change=change_persona,
            format_func=lambda x: x,
            index=list(persona_options.keys()).index(next(p["name"] for p in personas if p["key"] == st.session_state.current_persona))
        )
        
        # Store the actual key in session state
        if "persona_selector_display" in st.session_state:
            st.session_state.persona_selector = persona_options[st.session_state.persona_selector_display]
        
        # Performance stats
        with st.expander("Performance Stats"):
            stats = st.session_state.chatbot.get_performance_stats()
            for op_name, op_stats in stats.items():
                st.markdown(f"**{op_name}**")
                st.markdown(f"- Avg time: {op_stats['avg']:.3f}s")
                st.markdown(f"- Min/Max: {op_stats['min']:.3f}s / {op_stats['max']:.3f}s")
                st.markdown(f"- Calls: {op_stats['count']}")
    
    # Main chat interface
    st.header("Lab o Future Educational Assistant")
    
    # Display chat history
    display_chat_messages()
    
    # Chat input
    if prompt := st.chat_input("Ask a question about Lab o Future"):
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })
        
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Get response from chatbot
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.chatbot.get_response(prompt)
                st.markdown(response["text"])
                
                # Add response to chat history
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response["text"],
                    "metadata": response["metadata"]
                })


if __name__ == "__main__":
    main()