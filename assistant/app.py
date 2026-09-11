"""Streamlit interface for the AI Mobility Assistant."""

from __future__ import annotations

import streamlit as st

from assistant.analytics import answer_question, load_bundle, question_examples

st.set_page_config(page_title='Urban Flow | AI Mobility Assistant', page_icon='🧭', layout='wide')


def _apply_assistant_styles() -> None:
    """Add a small visual polish layer without changing assistant behavior."""
    st.html(
        """
        <style>
        .stApp {
            background: linear-gradient(135deg, #F8FBFC 0%, #EDF7F8 100%);
        }
        .block-container {
            max-width: 1180px;
            padding-top: 2rem;
            padding-bottom: 2.5rem;
        }
        [data-testid="stForm"] {
            margin-top: 1.25rem;
            padding: 1.15rem 1.2rem 1.25rem;
            border: 1px solid #BFD7DE;
            border-left: 4px solid #0B7189;
            border-radius: 12px;
            background: rgba(255, 255, 255, 0.92);
            box-shadow: 0 10px 24px rgba(23, 59, 83, 0.08);
        }
        [data-testid="stForm"] [data-testid="stTextInput"] input {
            min-height: 2.85rem;
            background: #FFFFFF;
        }
        [data-testid="stFormSubmitButton"] button {
            min-height: 2.75rem;
            font-weight: 650;
        }
        [data-testid="stChatMessage"] {
            margin: 0.75rem 0;
            padding: 0.35rem 0.65rem;
            border: 1px solid #D7E5E9;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.8);
            box-shadow: 0 5px 14px rgba(23, 59, 83, 0.04);
        }
        [data-testid="stSidebar"] [data-testid="stButton"] button {
            margin-bottom: 0.2rem;
            text-align: left;
        }
        </style>
        """
    )


_apply_assistant_styles()


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


def _select_example(question: str) -> None:
    """Place a sidebar example into the editable question field on rerun."""
    st.session_state.prompt = question


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
            st.button(
                example,
                use_container_width=True,
                key=f'example::{example}',
                on_click=_select_example,
                args=(example,),
            )
        st.subheader('Safety')
        st.write('No raw data, parquet files, model artifacts or arbitrary Python execution are exposed. Questions are routed to fixed analytics functions only.')

    st.info('Try asking about the busiest pickup zones, the best 24-hour forecast model, or what fleet managers should do during evening peaks.')

    for message in st.session_state.messages:
        _render_message(message)

    with st.form('assistant-form', clear_on_submit=False):
        question = st.text_input('Your question', key='prompt', placeholder='Ask about demand, routes, forecasts, or recommendations')
        submit = st.form_submit_button('Ask assistant')

    if submit and question.strip():
        response = answer_question(question, bundle)
        st.session_state.messages.append({'role': 'user', 'content': question})
        st.session_state.messages.append({'role': 'assistant', 'content': response.body})
        if response.table is not None and not response.table.empty:
            st.session_state.messages.append({'role': 'assistant', 'content': response.table.to_string(index=False)})
        st.rerun()


if __name__ == '__main__':
    main()
