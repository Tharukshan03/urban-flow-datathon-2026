"""Shared visual components for the two Urban Flow Streamlit interfaces."""

from __future__ import annotations

from html import escape
from typing import Iterable, Mapping

import streamlit as st


ACCENT = "#0B7189"
INK = "#172B3A"
MUTED = "#5C6F7D"


def apply_product_styles() -> None:
    """Apply compact, responsive presentation details beyond native theme tokens."""
    st.html(
        """
        <style>
        .stApp,
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(circle at 88% 4%, rgba(182, 231, 238, 0.46), transparent 30%),
                linear-gradient(135deg, #FFFFFF 0%, #F7FCFD 46%, #EAF5F9 100%);
            background-attachment: fixed;
        }
        .block-container {
            max-width: 1480px;
            padding-top: 1.45rem;
            padding-bottom: 2.5rem;
        }
        [data-testid="stSidebar"] { border-right: 1px solid #294A5D; }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] label { line-height: 1.35; }
        [data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(255, 255, 255, 0.92);
            box-shadow: 0 8px 24px rgba(20, 48, 66, 0.055);
        }
        [data-testid="stMetric"] {
            background: #FFFFFF;
            box-shadow: 0 8px 24px rgba(20, 48, 66, 0.055);
        }
        [data-testid="stMetricValue"] { color: #173B53; }
        [data-testid="stPlotlyChart"] { border-radius: 8px; overflow: hidden; }
        [data-testid="stForm"] {
            background: #FFFFFF;
            box-shadow: 0 8px 24px rgba(20, 48, 66, 0.055);
        }
        [data-testid="stTextInput"] input { min-height: 2.8rem; }
        .st-key-ask_assistant button { min-height: 2.8rem; font-weight: 650; }
        .st-key-clear_history button { color: #526775; }
        [data-testid="stToolbar"],
        [data-testid="stAppDeployButton"],
        [data-testid="stStatusWidget"],
        [data-testid="stHeaderActionElements"],
        [data-testid="stDecoration"],
        .stDeployButton {
            display: none !important;
        }
        footer { visibility: hidden; }
        .ufa-hero {
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            gap: 1.25rem;
            padding: 1.2rem 1.35rem;
            margin: 0 0 1.15rem;
            border: 1px solid #D7E0E7;
            border-left: 5px solid #0B7189;
            border-radius: 10px;
            background: #FFFFFF;
            box-shadow: 0 10px 30px rgba(20, 48, 66, 0.065);
        }
        .ufa-eyebrow {
            margin: 0 0 0.32rem;
            color: #0B7189;
            font-size: 0.74rem;
            font-weight: 750;
            letter-spacing: 0.11em;
            text-transform: uppercase;
        }
        .ufa-hero h1 {
            margin: 0;
            color: #173B53;
            font-size: clamp(1.65rem, 3vw, 2.35rem);
            line-height: 1.08;
        }
        .ufa-hero p {
            max-width: 760px;
            margin: 0.45rem 0 0;
            color: #5C6F7D;
            font-size: 0.98rem;
            line-height: 1.45;
        }
        .ufa-kpi-grid {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.7rem 0 1.15rem;
        }
        .ufa-kpi {
            min-width: 0;
            padding: 0.9rem 0.95rem;
            border: 1px solid #D7E0E7;
            border-top: 3px solid #0B7189;
            border-radius: 9px;
            background: #FFFFFF;
            box-shadow: 0 7px 22px rgba(20, 48, 66, 0.05);
        }
        .ufa-kpi-label {
            color: #657784;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.055em;
            text-transform: uppercase;
        }
        .ufa-kpi-value {
            margin-top: 0.33rem;
            color: #173B53;
            font-size: clamp(1.12rem, 1.7vw, 1.55rem);
            font-weight: 750;
            line-height: 1.14;
            overflow-wrap: anywhere;
        }
        .ufa-kpi-context {
            margin-top: 0.32rem;
            color: #657784;
            font-size: 0.76rem;
            line-height: 1.3;
        }
        .ufa-section-heading { margin: 0.2rem 0 0.9rem; }
        .ufa-section-heading h2 {
            margin: 0;
            color: #173B53;
            font-size: clamp(1.35rem, 2vw, 1.85rem);
        }
        .ufa-section-heading p {
            margin: 0.32rem 0 0;
            color: #657784;
            font-size: 0.91rem;
        }
        .ufa-sidebar-brand {
            margin: 0.15rem 0 1rem;
            padding: 0.2rem 0 0.8rem;
            border-bottom: 1px solid #294A5D;
        }
        .ufa-sidebar-brand .ufa-eyebrow { color: #7ED0D9; }
        .ufa-sidebar-brand h2 {
            margin: 0;
            color: #FFFFFF;
            font-size: 1.25rem;
            line-height: 1.12;
        }
        .ufa-sidebar-brand p {
            margin: 0.42rem 0 0;
            color: #C5D3DC;
            font-size: 0.82rem;
            line-height: 1.4;
        }
        .ufa-sidebar-status {
            display: inline-flex;
            align-items: center;
            margin-top: 0.65rem;
            padding: 0.26rem 0.54rem;
            border: 1px solid #39778A;
            border-radius: 999px;
            background: #173D4F;
            color: #C8F1E8;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .ufa-query-label {
            margin-bottom: 0.22rem;
            color: #0B7189;
            font-size: 0.69rem;
            font-weight: 750;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }
        .ufa-query-text {
            margin: 0 0 0.72rem;
            color: #173B53;
            font-size: 1rem;
            font-weight: 650;
        }
        @media (max-width: 1100px) {
            .ufa-kpi-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
        }
        @media (max-width: 760px) {
            .block-container { padding-top: 1rem; }
            .ufa-hero { flex-direction: column; gap: 0.7rem; }
            .ufa-kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        }
        </style>
        """
    )


def apply_assistant_styles() -> None:
    """Add stronger typography and raised query surfaces to the assistant."""
    st.html(
        """
        <style>
        [data-testid="stAppViewContainer"] .block-container p,
        [data-testid="stAppViewContainer"] .block-container li,
        [data-testid="stAppViewContainer"] .block-container label {
            font-size: 1.02rem;
            line-height: 1.55;
        }
        [data-testid="stAppViewContainer"] .block-container h3 {
            font-size: 1.35rem;
        }
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] button {
            font-size: 0.96rem;
        }
        .st-key-query_panel [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #C4D8DF;
            background: linear-gradient(145deg, #FFFFFF 0%, #F2F9FB 100%);
            box-shadow:
                0 13px 30px rgba(23, 59, 83, 0.12),
                inset 0 1px 0 rgba(255, 255, 255, 0.98),
                inset 0 -1px 0 rgba(118, 154, 168, 0.16);
        }
        .st-key-query_panel [data-testid="stTextInput"] input {
            min-height: 3.15rem;
            border: 1px solid #AFC8D1;
            background: linear-gradient(180deg, #FFFFFF 0%, #F6FAFC 100%);
            box-shadow:
                inset 0 2px 5px rgba(23, 59, 83, 0.10),
                0 5px 14px rgba(23, 59, 83, 0.09);
            font-size: 1.05rem;
        }
        .st-key-query_panel [data-testid="stTextInput"] input:focus {
            border-color: #0B7189;
            box-shadow:
                inset 0 2px 5px rgba(23, 59, 83, 0.08),
                0 0 0 3px rgba(11, 113, 137, 0.13),
                0 7px 17px rgba(23, 59, 83, 0.10);
        }
        [class*="st-key-history_"] [data-testid="stVerticalBlockBorderWrapper"] {
            border: 1px solid #C9DCE3;
            background: linear-gradient(145deg, #FFFFFF 0%, #F3F9FB 100%);
            box-shadow:
                0 10px 25px rgba(23, 59, 83, 0.10),
                inset 0 1px 0 rgba(255, 255, 255, 0.98),
                inset 0 -1px 0 rgba(118, 154, 168, 0.12);
        }
        .ufa-query-label { font-size: 0.76rem; }
        .ufa-query-text { font-size: 1.08rem; }
        @media (max-width: 760px) {
            [data-testid="stAppViewContainer"] .block-container p,
            [data-testid="stAppViewContainer"] .block-container li,
            [data-testid="stAppViewContainer"] .block-container label {
                font-size: 0.98rem;
            }
        }
        </style>
        """
    )


def hero(eyebrow: str, title: str, subtitle: str) -> None:
    st.html(
        f"""
        <div class="ufa-hero">
          <div>
            <div class="ufa-eyebrow">{escape(eyebrow)}</div>
            <h1>{escape(title)}</h1>
            <p>{escape(subtitle)}</p>
          </div>
        </div>
        """
    )


def sidebar_brand(product: str, description: str, status: str = "Data status: Verified") -> None:
    st.html(
        f"""
        <div class="ufa-sidebar-brand">
          <div class="ufa-eyebrow">Merge Conflicts</div>
          <h2>{escape(product)}</h2>
          <p>{escape(description)}</p>
          <div class="ufa-sidebar-status">{escape(status)}</div>
        </div>
        """
    )


def section_heading(title: str, subtitle: str) -> None:
    st.html(
        f"""
        <div class="ufa-section-heading">
          <h2>{escape(title)}</h2>
          <p>{escape(subtitle)}</p>
        </div>
        """
    )


def kpi_grid(cards: Iterable[Mapping[str, str]]) -> None:
    markup = []
    for card in cards:
        markup.append(
            "<div class='ufa-kpi'>"
            f"<div class='ufa-kpi-label'>{escape(card['label'])}</div>"
            f"<div class='ufa-kpi-value'>{escape(card['value'])}</div>"
            f"<div class='ufa-kpi-context'>{escape(card['context'])}</div>"
            "</div>"
        )
    st.html(f"<div class='ufa-kpi-grid'>{''.join(markup)}</div>")


def status_banner(title: str, detail: str) -> None:
    st.success(f"**{title}**  \n{detail}", icon=":material/check_circle:")


def query_card_header(question: str) -> None:
    st.html(
        f"""
        <div class="ufa-query-label">Query · Verified analytics response</div>
        <div class="ufa-query-text">{escape(question)}</div>
        <div class="ufa-query-label">Answer</div>
        """
    )
