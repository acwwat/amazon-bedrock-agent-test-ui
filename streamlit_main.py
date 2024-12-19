from dotenv import load_dotenv
import json
import os
from services import bedrock_agent_runtime
import streamlit as st
import uuid
import boto3

# Load environment variables from .env file
load_dotenv()

# Configure AWS session with default credentials
session = boto3.Session(region_name='ap-southeast-2')

# Get config from environment variables
agent_id = os.environ.get("BEDROCK_AGENT_ID")
agent_alias_id = os.environ.get("BEDROCK_AGENT_ALIAS_ID", "TSTALIASID") # TSTALIASID is the default test alias ID
ui_title = os.environ.get("BEDROCK_AGENT_TEST_UI_TITLE", "Agents for Amazon Bedrock Test UI")
ui_icon = os.environ.get("BEDROCK_AGENT_TEST_UI_ICON")

# Must be the first Streamlit command
st.set_page_config(page_title=ui_title, page_icon=ui_icon, layout="wide")

def init_state():
    st.session_state.session_id = str(uuid.uuid4())
    st.session_state.messages = []
    st.session_state.citations = []
    st.session_state.trace = {}

# General page initialization
st.title(ui_title)
if len(st.session_state.items()) == 0:
    init_state()

# Sidebar button to reset session state
with st.sidebar:
    if st.button("Reset Session"):
        init_state()

# Messages in the conversation
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Chat input that invokes the agent
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        placeholder.markdown("...")
        response = bedrock_agent_runtime.invoke_agent(
            agent_id,
            agent_alias_id,
            st.session_state.session_id,
            prompt
        )
        output_text = response["output_text"]

        # Add citations
        if len(response["citations"]) > 0:
            citation_num = 1
            num_citation_chars = 0
            citation_locs = []
            citations_map = {}
            
            # First pass: collect all citation positions and URLs
            citation_positions = []
            citation_urls = {}  # Store position -> URL mapping
            for citation in response["citations"]:
                end_span = citation["generatedResponsePart"]["textResponsePart"]["span"]["end"] + 1
                citation_positions.append(end_span)
                for retrieved_ref in citation["retrievedReferences"]:
                    url = retrieved_ref.get("metadata", {}).get("url", retrieved_ref["location"]["s3Location"]["uri"])
                    citation_urls[end_span] = url
            
            # Sort positions in reverse order to process from end to beginning
            citation_positions.sort(reverse=True)
            
            # Check if any position breaks a word
            for pos in citation_positions:
                if pos < len(output_text):
                    # Look for word boundary before and after position
                    left = output_text[:pos].rstrip()
                    right = output_text[pos:].lstrip()
                    
                    # If we're in the middle of a word, move position to end of word
                    if (left and right and 
                        left[-1].isalnum() and right[0].isalnum()):
                        # Find end of word
                        word_end = pos
                        while (word_end < len(output_text) and 
                               output_text[word_end].isalnum()):
                            word_end += 1
                        # Update the position in the citation
                        for citation in response["citations"]:
                            if citation["generatedResponsePart"]["textResponsePart"]["span"]["end"] + 1 == pos:
                                citation["generatedResponsePart"]["textResponsePart"]["span"]["end"] = word_end - 1
                                citation_urls[word_end] = citation_urls[pos]  # Update URL mapping

            # Now proceed with normal citation processing
            for citation in response["citations"]:
                end_span = citation["generatedResponsePart"]["textResponsePart"]["span"]["end"] + 1
                for retrieved_ref in citation["retrievedReferences"]:
                    article_url = retrieved_ref.get("metadata", {}).get("url", retrieved_ref["location"]["s3Location"]["uri"])
                    article_title = retrieved_ref.get("metadata", {}).get("title", "Article " + str(citation_num))
                    
                    citations_map[citation_num] = article_url
                    
                    # Create clickable citation marker
                    citation_marker = f' <a href="{article_url}" target="_blank" rel="noopener noreferrer">[{citation_num}]</a>'
                    
                    if end_span + num_citation_chars < len(output_text) and output_text[end_span + num_citation_chars] != ' ':
                        citation_marker = ' ' + citation_marker
                    
                    output_text = output_text[:end_span + num_citation_chars] + citation_marker + output_text[end_span + num_citation_chars:]
                    citation_locs.append((f"[{citation_num}]", article_url, article_title))
                    
                    citation_num = citation_num + 1
                    num_citation_chars = num_citation_chars + len(citation_marker)
                
                # Only add newline if we're not at the end of all citations
                if citation != response["citations"][-1]:
                    output_text = output_text[:end_span + num_citation_chars] + "\n" + output_text[end_span + num_citation_chars:]
                    num_citation_chars = num_citation_chars + 1
            
            # Add references section at the end with formatted links
            references = "\n\n---\n### References\n"
            for marker, url, title in citation_locs:
                references += f"{marker} [{title}]({url})\n"
            
            output_text = output_text + references

        placeholder.markdown(output_text, unsafe_allow_html=True)
        st.session_state.messages.append({"role": "assistant", "content": output_text})
        st.session_state.citations = response["citations"]
        st.session_state.trace = response["trace"]

trace_types_map = {
    "Pre-Processing": ["preGuardrailTrace", "preProcessingTrace"],
    "Orchestration": ["orchestrationTrace"],
    "Post-Processing": ["postProcessingTrace", "postGuardrailTrace"]
}

trace_info_types_map = {
    "preProcessingTrace": ["modelInvocationInput", "modelInvocationOutput"],
    "orchestrationTrace": ["invocationInput", "modelInvocationInput", "modelInvocationOutput", "observation", "rationale"],
    "postProcessingTrace": ["modelInvocationInput", "modelInvocationOutput", "observation"]
}

# Sidebar section for trace
with st.sidebar:
    st.title("Trace")

    # Show each trace types in separate sections
    step_num = 1
    for trace_type_header in trace_types_map:
        st.subheader(trace_type_header)

        # Organize traces by step similar to how it is shown in the Bedrock console
        has_trace = False
        for trace_type in trace_types_map[trace_type_header]:
            if trace_type in st.session_state.trace:
                has_trace = True
                trace_steps = {}

                for trace in st.session_state.trace[trace_type]:
                    # Each trace type and step may have different information for the end-to-end flow
                    if trace_type in trace_info_types_map:
                        trace_info_types = trace_info_types_map[trace_type]
                        for trace_info_type in trace_info_types:
                            if trace_info_type in trace:
                                trace_id = trace[trace_info_type]["traceId"]
                                if trace_id not in trace_steps:
                                    trace_steps[trace_id] = [trace]
                                else:
                                    trace_steps[trace_id].append(trace)
                                break
                    else:
                        trace_id = trace["traceId"]
                        trace_steps[trace_id] = [
                            {
                                trace_type: trace
                            }
                        ]

                # Show trace steps in JSON similar to the Bedrock console
                for trace_id in trace_steps.keys():
                    with st.expander(f"Trace Step " + str(step_num), expanded=False):
                        for trace in trace_steps[trace_id]:
                            trace_str = json.dumps(trace, indent=2)
                            st.code(trace_str, language="json", line_numbers=trace_str.count("\n"))
                    step_num = step_num + 1
        if not has_trace:
            st.text("None")

    st.subheader("Citations")
    if len(st.session_state.citations) > 0:
        citation_num = 1
        for citation in st.session_state.citations:
            for retrieved_ref_num, retrieved_ref in enumerate(citation["retrievedReferences"]):
                with st.expander("Citation [" + str(citation_num) + "]", expanded=False):
                    citation_str = json.dumps({
                        "generatedResponsePart": citation["generatedResponsePart"],
                        "retrievedReference": citation["retrievedReferences"][retrieved_ref_num]
                    }, indent=2)
                    st.code(citation_str, language="json", line_numbers=trace_str.count("\n"))
                citation_num = citation_num + 1
    else:
        st.text("None")