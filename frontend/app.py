import streamlit as st
import requests
import pandas as pd
import os
from datetime import datetime
BACKEND_URL = os.environ.get('BACKEND_URL', 'http://backend:8000')
st.set_page_config(page_title='AI Metadata-to-SQL', layout='wide')
st.title('AI Metadata-to-SQL Generator (Autonomous Mode)')
if 'token' not in st.session_state:
    st.session_state['token'] = None
if 'role' not in st.session_state:
    st.session_state['role'] = None
if 'username' not in st.session_state:
    st.session_state['username'] = None
with st.sidebar:
    st.header('Authentication')
    if st.session_state['token'] is None:
        username = st.text_input('Username', key='login_user')
        password = st.text_input('Password', type='password', key='login_pass')
        if st.button('Login'):
            try:
                resp = requests.post(f'{BACKEND_URL}/auth/token', data={'username': username, 'password': password}, timeout=20)
                resp.raise_for_status()
                data = resp.json()
                st.session_state['token'] = data.get('access_token')
                st.session_state['role'] = data.get('role')
                st.session_state['username'] = username
                st.success(f'Logged in as {username} ({st.session_state["role"]})')
            except Exception as e:
                st.error(f'Login failed: {e}')
    else:
        st.markdown(f"**Logged in:** {st.session_state.get('username')} \n Role: {st.session_state.get('role')}")
        if st.button('Logout'):
            try:
                headers = {'Authorization': f'Bearer {st.session_state.get("token")}' }
                resp = requests.post(f'{BACKEND_URL}/auth/logout', headers=headers, timeout=10)
                resp.raise_for_status()
                st.session_state['token'] = None
                st.session_state['role'] = None
                st.session_state['username'] = None
                st.success('Logged out')
                st.experimental_rerun()
            except Exception as e:
                st.error(f'Logout failed: {e}')
    st.markdown('---')
    st.header('Connection')
    db_type = st.selectbox('Select Database Type', ['postgresql','oracle','snowflake','teradata','db2'], index=0)
    conn_str = st.text_input('Connection string', value=os.environ.get('TARGET_DB_CONN',''))
    schema = st.text_input('Schema', value=os.environ.get('DEFAULT_SCHEMA','public'))
    if st.button('Validate Connection'):
        try:
            headers = {'Authorization': f'Bearer {st.session_state.get("token")}'}
            resp = requests.post(f'{BACKEND_URL}/connect', json={'conn_str': conn_str}, timeout=20, headers=headers)
            resp.raise_for_status()
            st.success('Connection OK')
        except Exception as e:
            st.error(f'Connection failed: {e}')
    if st.session_state.get('role') == 'admin':
        if st.button('Generate Metadata & Index'):
            try:
                headers = {'Authorization': f'Bearer {st.session_state.get("token")}'}
                resp = requests.post(f'{BACKEND_URL}/extract_metadata', json={'conn_str': conn_str, 'schema': schema, 'db_type': db_type}, timeout=120, headers=headers)
                resp.raise_for_status()
                st.success(f"Indexed {resp.json().get('count')} metadata entries")
            except Exception as e:
                st.error(f'Extraction failed: {e}')
        if st.button('Reload Schema (Admin only)'):
            try:
                headers = {'Authorization': f'Bearer {st.session_state.get("token")}'}
                resp = requests.post(f'{BACKEND_URL}/extract_metadata', json={'conn_str': conn_str, 'schema': schema, 'db_type': db_type}, timeout=120, headers=headers)
                resp.raise_for_status()
                st.success('Schema reloaded and re-indexed.')
            except Exception as e:
                st.error(f'Reload failed: {e}')
    else:
        st.info('Metadata extraction and schema reload are admin-only. Contact your admin to index schemas.')
st.header('Ask a question')
question = st.text_input('Enter natural language question', 'Find all actors who debuted after 2000')
col1, col2 = st.columns([3,1])
with col2:
    top_k = st.number_input('Top-K context', min_value=1, max_value=16, value=6)
    if st.button('Generate SQL'):
        if not conn_str or not question:
            st.error('Provide connection string and question')
        elif st.session_state.get('token') is None:
            st.error('Please login first')
        else:
            headers = {'Authorization': f'Bearer {st.session_state.get("token")}'}
            with st.spinner('Generating SQL...'):
                try:
                    resp = requests.post(f'{BACKEND_URL}/generate_sql', json={'conn_str': conn_str, 'schema': schema, 'question': question, 'top_k': top_k, 'db_type': db_type}, timeout=60, headers=headers)
                    resp.raise_for_status()
                    data = resp.json()
                    sql = data.get('sql')
                    context = data.get('context')
                    st.subheader('Generated SQL')
                    st.code(sql, language='sql')
                    if context:
                        st.subheader('Retrieved Schema Context')
                        for c in context:
                            st.markdown(f"**{c.get('id')}** — {c.get('document')}")
                    if st.button('Execute SQL'):
                        headers = {'Authorization': f'Bearer {st.session_state.get("token")}'}
                        exec_resp = requests.post(f'{BACKEND_URL}/execute_sql', json={'conn_str': conn_str, 'sql': sql}, timeout=120, headers=headers)
                        exec_resp.raise_for_status()
                        out = exec_resp.json()
                        df = pd.DataFrame(out['data'])
                        st.success(f"Returned {out['rows']} rows")
                        st.dataframe(df)
                        st.subheader('Chart view')
                        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]
                        if numeric_cols:
                            x = st.selectbox('X axis', options=df.columns, index=0)
                            y = st.selectbox('Y axis', options=numeric_cols, index=0)
                            import plotly.express as px
                            fig = px.bar(df, x=x, y=y)
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info('No numeric columns to chart')
                        st.download_button('Download CSV', data=out['csv'], file_name=f'result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
                except Exception as e:
                    st.error(f'Error: {e}')
if st.sidebar.button('Show my query history'):
    try:
        headers = {'Authorization': f'Bearer {st.session_state.get("token")}'}
        resp = requests.get(f'{BACKEND_URL}/history', timeout=20, headers=headers)
        resp.raise_for_status()
        history = resp.json().get('history', [])
        for h in history:
            st.sidebar.markdown(f"**{h.get('question')}** — {h.get('created_at')}\n```\n{h.get('sql')}\n```")
    except Exception as e:
        st.sidebar.error(f'Could not fetch history: {e}')
if st.session_state.get('role') == 'admin':
    if st.sidebar.button('Show all history'):
        try:
            headers = {'Authorization': f'Bearer {st.session_state.get("token")}' }
            resp = requests.get(f'{BACKEND_URL}/history?all=true', timeout=20, headers=headers)
            resp.raise_for_status()
            history = resp.json().get('history', [])
            st.subheader('All Query History')
            for h in history:
                st.markdown(f"**{h.get('question')}** — user:{h.get('user_id')} — {h.get('created_at')}\n```\n{h.get('sql')}\n```")
        except Exception as e:
            st.sidebar.error(f'Could not fetch all history: {e}')
    st.sidebar.markdown('---')
    st.sidebar.header('User Management (Admin Only)')
    new_username = st.sidebar.text_input('New Username')
    new_password = st.sidebar.text_input('New Password', type='password')
    new_role = st.sidebar.selectbox('Role', ['analyst', 'admin'])
    if st.sidebar.button('Create User'):
        try:
            headers = {'Authorization': f'Bearer {st.session_state.get("token")}'}
            resp = requests.post(f'{BACKEND_URL}/auth/create_user', params={'username': new_username, 'password': new_password, 'role': new_role}, headers=headers, timeout=20)
            resp.raise_for_status()
            st.sidebar.success(f"User '{new_username}' created as {new_role}")
        except Exception as e:
            st.sidebar.error(f"Could not create user: {e}")
