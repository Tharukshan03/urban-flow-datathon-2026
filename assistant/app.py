"""Streamlit interface for the AI Mobility Assistant."""

from __future__ import annotations

import streamlit as st

from assistant.analytics import answer_question, load_bundle, question_examples

st.set_page_config(page_title='Urban Flow | AI Mobility Assistant', page_icon='🧭', layout='wide')


def _init_state() -> None:
    if 'messages' not in st.session_state:
        st.session_state.messages = [
            {
                'role': 'assistant',
                'content': 'Ask a question about demand, routes, forecasts or recommendations. I will answer only from the verified bundled analytics snapshot.',
            }
        ]
    if 'prompt' not in st.session_state:
        st.session_state.prompt = ''
    if 'queued_question' not in st.session_state:
        st.session_state.queued_question = ''


def _render_message(message: dict[str, str]) -> None:
    with st.chat_message(message['role']):
        st.markdown(message['content'])


def main() -> None:
    _init_state()
    bundle = load_bundle()

    st.title('AI Mobility Assistant')
    st.caption('Bonus Track 5 · Safe question answering over verified taxi analytics inputs')

    with st.sidebar:
        st.header('Capabilities')
        st.write('The assistant answers questions about pickup hotspots, destination hotspots, borough demand, hourly and weekday demand, OD routes, time-window routes, forecast metrics, saved forecasts and operational recommendations.')
        st.subheader('Example questions')
        for example in question_examples():
            if st.button(example, use_container_width=True, key=f'example::{example}'):
                st.session_state.queued_question = example
        st.subheader('Safety')
        st.write('No raw data, parquet files, model artifacts or arbitrary Python execution are exposed. Questions are routed to fixed analytics functions only.')

    st.info('Try asking about the busiest pickup zones, the best 24-hour forecast model, or what fleet managers should do during evening peaks.')

    for message in st.session_state.messages:
        _render_message(message)

    with st.form('assistant-form', clear_on_submit=False):
        default_question = st.session_state.queued_question or st.session_state.prompt
        question = st.text_input('Your question', key='prompt', value=default_question, placeholder='Ask about demand, routes, forecasts, or recommendations')
        submit = st.form_submit_button('Ask assistant')

    if submit and question.strip():
        response = answer_question(question, bundle)
        st.session_state.messages.append({'role': 'user', 'content': question})
        st.session_state.messages.append({'role': 'assistant', 'content': response.body})
        if response.table is not None and not response.table.empty:
            st.session_state.messages.append({'role': 'assistant', 'content': response.table.to_string(index=False)})
        st.session_state.queued_question = ''
        st.rerun()


if __name__ == '__main__':
    main()
