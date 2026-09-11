"""Streamlit interface for the deterministic AI Mobility Assistant."""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd
import streamlit as st

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from assistant.analytics import AssistantBundle, answer_question, load_bundle
from src.streamlit_ui import (
    apply_assistant_styles,
    apply_product_styles,
    hero,
    query_card_header,
    sidebar_brand,
)

st.set_page_config(
    page_title='Urban Flow | Verified mobility assistant',
    page_icon=':material/assistant:',
    layout='wide',
)
apply_product_styles()
apply_assistant_styles()

EXAMPLE_QUESTIONS = (
    'What are the top 5 pickup zones?',
    'Which forecasting model should we use for 24 hours?',
    'What is the 24-hour forecast for JFK Airport?',
    'What should fleet managers do during evening peaks?',
)


def _init_state() -> None:
    st.session_state.setdefault('assistant_query', '')
    st.session_state.setdefault('query_history', [])
    st.session_state.setdefault('query_notice', '')


def _select_example(question: str) -> None:
    """Populate the widget-bound query before the next input render."""
    st.session_state['assistant_query'] = question
    st.session_state['query_notice'] = ''


def _submit_query(bundle: AssistantBundle) -> None:
    """Run one predefined analytics route and prepend it to session history."""
    question = st.session_state.get('assistant_query', '').strip()
    if not question:
        st.session_state['query_notice'] = 'Enter a mobility question before submitting.'
        return

    response = answer_question(question, bundle)
    table = None if response.table is None else response.table.copy()
    st.session_state['query_history'].insert(
        0,
        {'question': question, 'answer': response.body, 'table': table},
    )
    st.session_state['assistant_query'] = ''
    st.session_state['query_notice'] = ''


def _clear_history() -> None:
    st.session_state['query_history'] = []
    st.session_state['query_notice'] = ''


def _render_history() -> None:
    history = st.session_state['query_history']
    heading, action = st.columns([4, 1], vertical_alignment='center')
    heading.subheader('Analysis history')
    action.button(
        'Clear history',
        key='clear_history',
        icon=':material/delete_sweep:',
        on_click=_clear_history,
        disabled=not history,
        width='stretch',
    )

    if not history:
        with st.container(border=True):
            st.markdown('**No completed queries in this session**')
            st.caption('Choose an example or enter a question above. Verified responses will appear here.')
        return

    for index, entry in enumerate(history):
        with st.container(border=True, key=f'history_{index}'):
            query_card_header(entry['question'])
            st.markdown(entry['answer'])
            table = entry['table']
            if isinstance(table, pd.DataFrame) and not table.empty:
                st.dataframe(table, hide_index=True, width='stretch')


def main() -> None:
    _init_state()
    bundle = load_bundle()

    with st.sidebar:
        sidebar_brand(
            'Urban Flow AI Assistant',
            'Bounded question answering over verified competition analytics.',
            'Verified data only',
        )
        st.markdown('##### Example questions')
        st.caption('Select a question to place it in the editable query field.')
        for index, example in enumerate(EXAMPLE_QUESTIONS):
            st.button(
                example,
                key=f'example_{index}',
                on_click=_select_example,
                args=(example,),
                width='stretch',
            )
        st.markdown('##### Safety boundary')
        st.caption(
            'Deterministic intent routing · predefined analytics functions · '
            'no raw trip access · no arbitrary Python · no unrestricted SQL'
        )

    hero(
        'Urban Flow AI Assistant',
        'Verified mobility intelligence',
        'Ask about hotspots, demand patterns, OD flows, forecasting, and operational recommendations.',
    )

    with st.container(border=True, key='query_panel'):
        st.subheader('Ask a mobility question')
        st.caption('Responses are generated from checksum-validated bundled analytics inputs.')
        st.text_input(
            'Mobility question',
            key='assistant_query',
            placeholder='Ask about pickup hotspots, forecasts, OD flows, or demand patterns...',
            icon=':material/search:',
        )
        st.button(
            'Ask assistant',
            key='ask_assistant',
            type='primary',
            icon=':material/arrow_forward:',
            on_click=_submit_query,
            args=(bundle,),
            width='stretch',
        )
        if st.session_state['query_notice']:
            st.warning(st.session_state['query_notice'], icon=':material/info:')

    _render_history()
    st.caption('Bonus Track 5 · Deterministic analytics interface · Verified bundled inputs only')


if __name__ == '__main__':
    main()
