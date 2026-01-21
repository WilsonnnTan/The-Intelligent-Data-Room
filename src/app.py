"""
The Intelligent Data Room
A multi-agent web application for conversational data analysis.

This application allows users to upload CSV/XLSX files and interact with their 
data using natural language. It uses a Planner-Executor agent architecture with
Google Gemini and PandasAI

Author: Wilson Angelie Tan
"""

import os
import sys
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv
import pandas as pd

from agents.orchestrator import AgentOrchestrator

# Load environment variables
load_dotenv()


# Page Configuration
st.set_page_config(
    page_title="Intelligent Data Room",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS Styling
st.markdown("""
<style>
    /* Main container styling */
    .main > div {
        padding-top: 2rem;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem 2rem;
        border-radius: 16px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 20px rgba(102, 126, 234, 0.3);
    }
    
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
    }
    
    .main-header p {
        color: rgba(255, 255, 255, 0.9);
        margin: 0.5rem 0 0 0;
        font-size: 1rem;
    }
    
    /* Chat message styling */
    .chat-message {
        padding: 1rem 1.5rem;
        margin: 0.75rem 0;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
    
    .user-message {
        background: linear-gradient(135deg, #f5f7fa 0%, #e8ecf3 100%);
        border-left: 4px solid #667eea;
    }
    
    .assistant-message {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border-left: 4px solid #10b981;
    }
    
    /* Plan display styling */
    .plan-container {
        background: linear-gradient(135deg, #fef9c3 0%, #fef3c7 100%);
        padding: 1rem 1.5rem;
        border-radius: 12px;
        margin: 0.75rem 0;
        border-left: 4px solid #f59e0b;
    }
    
    /* Sidebar styling */
    .sidebar-section {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 1rem;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* File uploader styling */
    .stFileUploader > div {
        border-radius: 12px;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #374151;
    }
    
    /* Data preview styling */
    .dataframe {
        font-size: 0.85rem;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        color: #9ca3af;
        padding: 2rem 0;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


# Session State Initialization
def init_session_state():
    """Initialize Streamlit session state variables."""
    if "orchestrator" not in st.session_state:
        st.session_state.orchestrator = AgentOrchestrator()
    
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "data_loaded" not in st.session_state:
        st.session_state.data_loaded = False
    
    if "file_name" not in st.session_state:
        st.session_state.file_name = None

init_session_state()

# Sidebar
with st.sidebar:
    st.markdown("### Data Upload")
    
    uploaded_file = st.file_uploader(
        "Upload your data file",
        type=["csv", "xlsx", "xls"],
        help="Supported formats: CSV, XLSX (Max 10MB)"
    )
    
    if uploaded_file is not None:
        # Check if it's a new file
        if st.session_state.file_name != uploaded_file.name:
            with st.spinner("Loading data..."):
                success, message = st.session_state.orchestrator.load_data(
                    uploaded_file, 
                    uploaded_file.name
                )
            
            if success:
                st.session_state.data_loaded = True
                st.session_state.file_name = uploaded_file.name
                st.session_state.messages = []  # Clear chat for new file
                st.success(f"{message}")
            else:
                st.error(f"{message}")
    
    # Show data info if loaded
    if st.session_state.data_loaded:
        st.markdown("---")
        st.markdown("### Data Info")
        
        df_preview = st.session_state.orchestrator.get_data_preview()
        if df_preview is not None:
            st.write(f"**File:** {st.session_state.file_name}")
            st.write(f"**Rows:** {len(st.session_state.orchestrator.current_df):,}")
            st.write(f"**Columns:** {len(st.session_state.orchestrator.current_df.columns)}")
            
            with st.expander("View Data Schema"):
                schema = st.session_state.orchestrator.get_data_schema()
                st.code(schema, language="text")
            
            with st.expander("Preview Data"):
                st.dataframe(df_preview, use_container_width=True)
    
    # Clear conversation button
    st.markdown("---")
    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.orchestrator.clear_conversation()
        st.rerun()
    
    # Sample prompts
    st.markdown("---")
    st.markdown("### Sample Prompts")
    
    sample_prompts = [
        "Create a bar chart showing total Sales by Category",
        "What are the top 5 products by profit?",
        "Show the sales trend over time",
        "Which region has the highest sales?",
        "Is there a correlation between Discount and Profit?"
    ]
    
    for prompt in sample_prompts:
        if st.button(prompt, key=f"prompt_{hash(prompt)}", use_container_width=True):
            st.session_state.pending_prompt = prompt


# Header
st.markdown("""
<div class="main-header">
    <h1>Intelligent Data Room</h1>
    <p>Upload your data and ask questions in natural language. Our AI agents will analyze and visualize your data.</p>
</div>
""", unsafe_allow_html=True)

# Agent architecture explanation
with st.expander("How it works - Multi-Agent System"):
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        #### Agent 1: The Planner
        - Analyzes your natural language question
        - Understands the data schema
        - Creates a step-by-step execution plan
        - Determines if visualization is needed
        """)
    
    with col2:
        st.markdown("""
        #### Agent 2: The Executor  
        - Follows the execution plan
        - Uses PandasAI + Gemini to write Python code
        - Executes queries on your data
        - Generates charts with Plotly
        """)

# Check if data is loaded
if not st.session_state.data_loaded:
    st.info("Please upload a CSV or XLSX file using the sidebar to get started.")
else:
    # Display chat messages
    for message in st.session_state.messages:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.markdown(message["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                # Show execution plan if available
                if message.get("plan"):
                    with st.expander("Execution Plan", expanded=False):
                        st.markdown(message["plan"])
                
                # Show answer
                st.markdown(message["content"])
                
                # Show chart if available
                if message.get("chart") is not None:
                    st.plotly_chart(message["chart"], use_container_width=True)
                
                # Show result dataframe if available
                if message.get("result_df") is not None and not message["result_df"].empty:
                    with st.expander("📊 View Data Table"):
                        st.dataframe(message["result_df"], use_container_width=True)
    
    # Handle pending prompt from sidebar
    if hasattr(st.session_state, 'pending_prompt') and st.session_state.pending_prompt:
        prompt = st.session_state.pending_prompt
        st.session_state.pending_prompt = None
        
        # Add to messages and process
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking... Planning... Executing..."):
                result = st.session_state.orchestrator.process_query(prompt)
            
            if result.get("plan_display"):
                with st.expander("Execution Plan", expanded=True):
                    st.markdown(result["plan_display"])
            
            if result["success"]:
                st.markdown(result["answer"])
                
                if result["chart"] is not None:
                    st.plotly_chart(result["chart"], use_container_width=True)
                
                if result["result_df"] is not None and not result["result_df"].empty:
                    with st.expander("📊 View Data Table"):
                        st.dataframe(result["result_df"], use_container_width=True)
            else:
                st.error(result.get("error", "An error occurred."))
            
            # Add to messages
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "plan": result.get("plan_display"),
                "chart": result.get("chart"),
                "result_df": result.get("result_df")
            })
        
        st.rerun()
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)
        
        # Process with agents
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking... Planning... Executing..."):
                result = st.session_state.orchestrator.process_query(prompt)
            
            # Show execution plan
            if result.get("plan_display"):
                with st.expander("Execution Plan", expanded=True):
                    st.markdown(result["plan_display"])
            
            if result["success"]:
                st.markdown(result["answer"])
                
                # Show chart if generated
                if result["chart"] is not None:
                    st.plotly_chart(result["chart"], use_container_width=True)
                
                # Show result data if available
                if result["result_df"] is not None and not result["result_df"].empty:
                    with st.expander("📊 View Data Table"):
                        st.dataframe(result["result_df"], use_container_width=True)
            else:
                st.error(result.get("error", "An error occurred."))
            
            # Add assistant response to messages
            st.session_state.messages.append({
                "role": "assistant",
                "content": result["answer"],
                "plan": result.get("plan_display"),
                "chart": result.get("chart"),
                "result_df": result.get("result_df")
            })

# Footer
st.markdown("""
<div class="footer">
    <p>Built with Streamlit • Powered by Google Gemini & PandasAI</p>
</div>
""", unsafe_allow_html=True)
