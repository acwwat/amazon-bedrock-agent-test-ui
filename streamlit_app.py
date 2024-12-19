import streamlit as st
from services.bedrock_agent_runtime import BedrockAgentRuntime
import os
from dotenv import load_dotenv

def configure_app():
    # Load environment variables
    load_dotenv()
    
    st.set_page_config(
        page_title=os.getenv('BEDROCK_AGENT_TEST_UI_TITLE', "Bedrock Chat"),
        page_icon=os.getenv('BEDROCK_AGENT_TEST_UI_ICON', "🤖"),
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Add health check endpoint - handle both old and new Streamlit versions
    try:
        # Try new version first
        params = st.query_params
    except AttributeError:
        # Fall back to experimental version
        params = st.experimental_get_query_params()
    
    health_check = params.get('health')
    if health_check and (health_check == 'check' or health_check == ['check']):
        st.success('OK')
        st.stop()

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "agent" not in st.session_state:
        st.session_state.agent = BedrockAgentRuntime()

def display_chat_interface():
    # Sidebar
    with st.sidebar:
        st.title("Settings")
        st.write("Agent ID:", os.getenv('BEDROCK_AGENT_ID'))
        st.write("Agent Alias ID:", os.getenv('BEDROCK_AGENT_ALIAS_ID'))
        
        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.rerun()

def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def main():
    configure_app()
    initialize_session_state()
    
    st.title(os.getenv('BEDROCK_AGENT_TEST_UI_TITLE', "Bedrock Chat"))
    
    # Display sidebar and settings
    display_chat_interface()
    
    # Display chat messages
    display_chat_messages()
    
    # Chat input
    if prompt := st.chat_input("What would you like to know?"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
            
        # Get agent response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = st.session_state.agent.invoke_agent(prompt)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main() 