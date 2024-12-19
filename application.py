import os
import sys
from streamlit.web.bootstrap import run
import streamlit.web.bootstrap as bootstrap
import streamlit as st

def main():
    st.title("Bedrock Chat")
    # Your main application code here

def application(environ, start_response):
    try:
        os.environ['PYTHONPATH'] = '/var/app/current'
        bootstrap.load_config_options(flag_options={
            "server.port": 8501,
            "server.address": "0.0.0.0",
            "server.baseUrlPath": "",
            "browser.serverAddress": "0.0.0.0",
        })
        
        run(
            main_script_path="streamlit_app.py",
            command_line=[],
            args=[],
            flag_options={}
        )
        
        start_response('200 OK', [('Content-Type', 'text/html')])
        return [b"Streamlit is running"]
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        start_response('500 Internal Server Error', [('Content-Type', 'text/html')])
        return [str(e).encode('utf-8')] 

if __name__ == "__main__":
    main()