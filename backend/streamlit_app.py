
import streamlit as st
import folium
import streamlit.components.v1 as components
from geopy.geocoders import Nominatim
import math
import json
import html
import hashlib
from datetime import datetime
from io import BytesIO

import pandas as pd
import requests

from future_risk import analyze_future_flood
from landslide_pipeline import analyze_landslide


# ============================================================
# DISASTERLENS AI — FINAL STREAMLIT FRONTEND
# ============================================================
# Pages:
#   1. Dashboard  -> Flood + Landslide together
#   2. Flood      -> Flood-only intelligence
#   3. Landslide  -> Landslide-only intelligence
#   4. Analytics  -> Interactive current-analysis analytics
#   5. Weather    -> Live weather + forecast intelligence
#   6. Alerts     -> Derived hazard/weather alert center
#   7. Reports    -> Interactive report preview + downloads
#
# Existing working backend/model functions are intentionally
# reused. No model thresholds or prediction logic are changed.
# ============================================================

st.set_page_config(
    page_title="DisasterLens AI",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# GLOBAL CSS
# ============================================================

st.html(
    """
<style>

:root {
    --bg: #050c14;
    --panel: #091522;
    --panel-2: #0c1a29;
    --panel-3: #0f1e2e;
    --border: #1c3348;
    --border-soft: #173047;
    --text: #edf5fb;
    --muted: #7f96aa;
    --muted-2: #60788e;
    --blue: #2788ff;
    --flood: #1688ff;
    --flood-bright: #36a8ff;
    --slide: #ff3f4f;
    --slide-bright: #ff6b75;
    --green: #35df88;
    --yellow: #f5c84c;
    --orange: #ff9f32;
}

.stApp {
    background:
        radial-gradient(circle at 52% -5%, #12263a 0%, #07111d 34%, #050b12 75%);
    color: var(--text);
}

.main .block-container {
    max-width: 100%;
    padding: 0.65rem 0.85rem 0.45rem 0.85rem;
}

div[data-testid="stVerticalBlock"] {
    gap: 0.35rem;
}

div[data-testid="stHorizontalBlock"] {
    gap: 0.55rem;
}

section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #071521 0%, #06101a 100%);
    border-right: 1px solid #193047;
}

section[data-testid="stSidebar"] > div {
    padding: 0.55rem 0.55rem 0.5rem 0.55rem;
}

section[data-testid="stSidebar"] .stButton {
    margin: 0;
}

section[data-testid="stSidebar"] .stButton > button {
    min-height: 37px;
    height: 37px;
    padding: 0.35rem 0.65rem;
    justify-content: flex-start;
    text-align: left;
    border-radius: 8px;
    background: transparent;
    border: 1px solid transparent;
    color: #9eb2c5;
    font-size: 0.82rem;
    font-weight: 600;
    box-shadow: none;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    color: #fff;
    background: #0d2235;
    border-color: #1b3b56;
}

section[data-testid="stSidebar"] .stButton.nav-active > button {
    color: #fff;
    background: linear-gradient(135deg, #1653a0, #103c77);
    border-color: #2579d2;
    box-shadow: 0 5px 18px rgba(0,100,220,.18);
}

.brand-box {
    padding: 0.35rem 0.45rem 0.65rem;
    border-bottom: 1px solid #173047;
    margin-bottom: 0.45rem;
}

.brand-row {
    display: flex;
    align-items: center;
    gap: 10px;
}

.brand-logo {
    width: 42px;
    height: 42px;
    border-radius: 11px;
    display: grid;
    place-items: center;
    font-size: 22px;
    background: linear-gradient(145deg, #123b69, #0b223c);
    border: 1px solid #245a8c;
}

.brand-name {
    color: #f4f8fc;
    font-size: 1.08rem;
    font-weight: 850;
    letter-spacing: -0.02em;
}

.brand-sub {
    color: #71899e;
    font-size: 0.62rem;
    line-height: 1.35;
    margin-top: 2px;
}

.nav-label {
    color: #5f7890;
    font-size: 0.58rem;
    font-weight: 800;
    letter-spacing: .12em;
    padding: 0.35rem 0.35rem 0.22rem;
}

.status-box {
    margin-top: 0.55rem;
    padding: 0.65rem;
    border: 1px solid #1b354b;
    border-radius: 10px;
    background: linear-gradient(145deg, #0b1928, #08131f);
}

.status-head {
    color: var(--green);
    font-size: 0.66rem;
    font-weight: 800;
    margin-bottom: 5px;
}

.status-line {
    color: #8198ac;
    font-size: 0.59rem;
    margin: 3px 0;
}

.status-line b {
    color: #dce8f2;
}

.top-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 55px;
    padding: 0 0.2rem;
}

.title {
    color: #f4f8fc;
    font-size: 1.62rem;
    line-height: 1.05;
    font-weight: 850;
    letter-spacing: -.035em;
}

.subtitle {
    color: #8197ab;
    font-size: .73rem;
    margin-top: 4px;
}

.top-meta {
    display: flex;
    align-items: center;
    gap: 8px;
}

.live-pill {
    border: 1px solid rgba(53,223,136,.35);
    background: rgba(53,223,136,.10);
    color: #45e98f;
    border-radius: 18px;
    padding: 6px 10px;
    font-size: .62rem;
    font-weight: 800;
}

.location-pill {
    max-width: 240px;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    border: 1px solid #1d354a;
    background: #091723;
    color: #9db1c2;
    border-radius: 18px;
    padding: 6px 10px;
    font-size: .62rem;
}

.search-wrap {
    background: linear-gradient(145deg, #091724, #07121e);
    border: 1px solid #1c3449;
    border-radius: 11px;
    padding: 5px;
    margin: 0.15rem 0 0.35rem;
}

div[data-testid="stTextInput"] {
    margin-bottom: 0 !important;
}

div[data-testid="stTextInput"] input {
    background: #0c1825 !important;
    color: #edf5fb !important;
    border: 1px solid #20394f !important;
    border-radius: 8px !important;
    height: 39px !important;
    font-size: .82rem !important;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #2689ff !important;
    box-shadow: 0 0 0 1px #2689ff !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #60778c !important;
}

/* Location suggestion dropdown */
div[data-testid="stSelectbox"] {
    margin-bottom: 0 !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: #0c1825 !important;
    border: 1px solid #20394f !important;
    border-radius: 8px !important;
    min-height: 39px !important;
    color: #edf5fb !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] input {
    color: #edf5fb !important;
}
div[data-testid="stSelectbox"] [data-baseweb="select"] div {
    color: #edf5fb;
}

.search-wrap div[data-testid="stButton"] button,
div[data-testid="stFormSubmitButton"] button {
    height: 39px !important;
    border-radius: 8px !important;
    background: linear-gradient(135deg, #167dff, #0759c6) !important;
    border: 1px solid #278cff !important;
    color: #fff !important;
    font-size: .76rem !important;
    font-weight: 800 !important;
}

.page-card {
    background: linear-gradient(145deg, #0a1826, #07121e);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px;
}

.map-card {
    background: #081521;
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 8px;
    overflow: hidden;
}

.map-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1px 3px 7px;
}

.map-title {
    color: #edf5fb;
    font-size: .93rem;
    font-weight: 800;
}

.map-sub {
    color: #698196;
    font-size: .59rem;
    margin-top: 2px;
}

.layer-chip {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 5px 8px;
    border-radius: 14px;
    font-size: .58rem;
    font-weight: 800;
    border: 1px solid #234056;
    background: #0b1927;
    color: #9bb0c1;
}

.hazard-heading {
    color: #627b90;
    font-size: .58rem;
    font-weight: 850;
    letter-spacing: .11em;
    margin: 1px 0 5px;
}

.hazard-card {
    min-height: 67px;
    padding: 9px;
    border-radius: 10px;
    background: linear-gradient(145deg, #0b1a29, #081521);
    border: 1px solid #1a3348;
}

.hazard-card.flood {
    border-left: 3px solid var(--flood);
}

.hazard-card.slide {
    border-left: 3px solid var(--slide);
}

.hazard-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.hazard-name {
    color: #eaf3f9;
    font-size: .74rem;
    font-weight: 800;
}

.risk-badge {
    padding: 3px 6px;
    border-radius: 5px;
    font-size: .51rem;
    font-weight: 900;
    letter-spacing: .04em;
}

.risk-low {
    color: #49e796;
    background: rgba(53,223,136,.11);
}

.risk-medium {
    color: #f7ca52;
    background: rgba(247,202,82,.12);
}

.risk-high {
    color: #ff6871;
    background: rgba(255,63,79,.12);
}

.risk-unknown {
    color: #8ca0b2;
    background: rgba(140,160,178,.10);
}

.hazard-coverage {
    color: #dbe7ef;
    font-size: .83rem;
    font-weight: 750;
    margin-top: 7px;
}

.hazard-foot {
    color: #637b90;
    font-size: .53rem;
    margin-top: 1px;
}

.analysis-title {
    color: #f0f6fa;
    font-size: .83rem;
    font-weight: 820;
}

.analysis-sub {
    color: #688096;
    font-size: .58rem;
    margin-top: 2px;
}

.gauge {
    height: 88px;
    margin: 4px 0 1px;
    position: relative;
    overflow: hidden;
}

.gauge-arc {
    position: absolute;
    width: 132px;
    height: 132px;
    left: 50%;
    top: 2px;
    transform: translateX(-50%);
    border-radius: 50%;
    background: conic-gradient(
        from 270deg,
        #36d983 0deg,
        #b7dc45 48deg,
        #f4cb48 82deg,
        #ff9b3b 120deg,
        #ff3d48 180deg,
        transparent 180deg,
        transparent 360deg
    );
}

.gauge-arc:after {
    content: "";
    position: absolute;
    inset: 15px;
    border-radius: 50%;
    background: #091622;
    border: 1px solid #173047;
}

.gauge-label {
    position: absolute;
    left: 0;
    right: 0;
    bottom: 3px;
    text-align: center;
    z-index: 3;
}

.gauge-risk {
    font-size: 14px;
    font-weight: 900;
}

.gauge-score {
    color: #7b91a4;
    font-size: .52rem;
    margin-top: 2px;
}

.metric-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
}

.metric {
    background: #0b1927;
    border: 1px solid #193247;
    border-radius: 7px;
    padding: 7px;
}

.metric-label {
    color: #60788d;
    font-size: .48rem;
    text-transform: uppercase;
    letter-spacing: .06em;
}

.metric-value {
    color: #e4edf4;
    font-size: .7rem;
    font-weight: 750;
    margin-top: 3px;
}

.mini-section {
    color: #637b90;
    font-size: .52rem;
    font-weight: 850;
    letter-spacing: .1em;
    margin: 7px 0 4px;
}

.future-row {
    display: grid;
    grid-template-columns: 48px 1fr 45px;
    align-items: center;
    gap: 5px;
    background: #0b1927;
    border: 1px solid #193247;
    border-radius: 7px;
    padding: 6px 7px;
    margin-bottom: 4px;
}

.future-time {
    color: #8298aa;
    font-size: .48rem;
    font-weight: 800;
}

.future-score {
    color: #dce7ef;
    font-size: .64rem;
    font-weight: 750;
}

.future-level {
    text-align: right;
    font-size: .48rem;
    font-weight: 900;
}

.compact-strip {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 6px;
}

.strip-card {
    background: #0a1826;
    border: 1px solid #1a3348;
    border-radius: 9px;
    padding: 8px;
}

.strip-title {
    color: #6b8398;
    font-size: .5rem;
    font-weight: 850;
    letter-spacing: .08em;
}

.strip-value {
    color: #dfeaf2;
    font-size: .67rem;
    font-weight: 750;
    margin-top: 4px;
}

.error-box {
    border: 1px solid rgba(255,80,90,.3);
    background: rgba(255,50,60,.07);
    color: #ff8a91;
    border-radius: 8px;
    padding: 8px;
    font-size: .62rem;
}

.loading-box {
    border: 1px solid #21466a;
    background: rgba(39,136,255,.06);
    color: #82bfff;
    border-radius: 8px;
    padding: 9px;
    font-size: .62rem;
}

.detail-card {
    background: linear-gradient(145deg, #0a1826, #07121e);
    border: 1px solid #1c3449;
    border-radius: 12px;
    padding: 10px;
}

.detail-card.flood-detail {
    border-top: 2px solid var(--flood);
}

.detail-card.slide-detail {
    border-top: 2px solid var(--slide);
}

.detail-head {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 7px;
}

.detail-title {
    color: #eff6fa;
    font-size: .83rem;
    font-weight: 850;
}

.detail-tag {
    color: #7e95a8;
    font-size: .52rem;
}

.info-line {
    display: flex;
    justify-content: space-between;
    gap: 8px;
    padding: 5px 0;
    border-bottom: 1px solid #142b3d;
}

.info-line:last-child {
    border-bottom: 0;
}

.info-label {
    color: #71899d;
    font-size: .56rem;
}

.info-value {
    color: #dce8f0;
    font-size: .58rem;
    font-weight: 750;
    text-align: right;
}

.page-note {
    color: #5f778b;
    font-size: .54rem;
    line-height: 1.4;
}

.footer {
    text-align: center;
    color: #526a7e;
    font-size: .53rem;
    padding: 5px 0 1px;
}

div[data-testid="stAlert"] {
    padding: .45rem .7rem;
}

/* ========================================================
   SYSTEM PAGES
   ======================================================== */

.system-hero {
    background: linear-gradient(145deg, #0a1928, #07121e);
    border: 1px solid #1c3449;
    border-radius: 12px;
    padding: 12px 14px;
    margin-bottom: 8px;
}

.system-hero-title {
    color: #f2f7fb;
    font-size: 1rem;
    font-weight: 850;
}

.system-hero-sub {
    color: #71889b;
    font-size: .62rem;
    margin-top: 3px;
}

.system-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 7px;
}

.system-stat {
    background: #0a1826;
    border: 1px solid #1a3348;
    border-radius: 9px;
    padding: 9px;
}

.system-stat-label {
    color: #60788d;
    font-size: .49rem;
    font-weight: 850;
    text-transform: uppercase;
    letter-spacing: .06em;
}

.system-stat-value {
    color: #e5eef5;
    font-size: .86rem;
    font-weight: 850;
    margin-top: 4px;
}

.alert-item {
    background: #0a1826;
    border: 1px solid #1b3448;
    border-left: 3px solid #71889b;
    border-radius: 9px;
    padding: 9px 10px;
    margin-bottom: 6px;
}

.alert-item.high { border-left-color: #ff3f4f; }
.alert-item.medium { border-left-color: #f5c84c; }
.alert-item.low { border-left-color: #35df88; }

.alert-title {
    color: #eaf3f9;
    font-size: .7rem;
    font-weight: 850;
}

.alert-text {
    color: #7890a3;
    font-size: .58rem;
    line-height: 1.4;
    margin-top: 3px;
}

.report-preview {
    background: #f7f9fb;
    color: #152231;
    border-radius: 10px;
    padding: 18px;
    border: 1px solid #d7e0e8;
}

.report-preview h2 { margin: 0 0 4px; font-size: 20px; }
.report-preview h3 { margin: 14px 0 6px; font-size: 13px; }
.report-preview p, .report-preview td { font-size: 11px; }
.report-preview table { width:100%; border-collapse:collapse; }
.report-preview td { padding:5px 6px; border-bottom:1px solid #dfe6ec; }
.report-preview td:first-child { font-weight:700; width:38%; }

@media (max-width: 1000px) {
    .title { font-size: 1.35rem; }
    .compact-strip { grid-template-columns: 1fr 1fr; }
}


/* ============================================================
   DISASTERLENS COMMAND CENTER — VISUAL POLISH
   Visual-only layer: no model/API/data logic changes.
   ============================================================ */

body, .stApp {
    font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                 "Segoe UI", sans-serif;
}

.stApp {
    background:
        radial-gradient(circle at 52% -15%, rgba(26,91,145,.28), transparent 34%),
        linear-gradient(180deg, #040b13 0%, #06111b 48%, #040a11 100%);
}

.main .block-container {
    max-width: 1520px;
    padding: .55rem .9rem .7rem;
}

section[data-testid="stSidebar"] {
    min-width: 255px;
    max-width: 255px;
    background:
        radial-gradient(circle at 50% 0%, rgba(16,67,105,.18), transparent 32%),
        linear-gradient(180deg, #06131f 0%, #04101a 100%);
    border-right: 1px solid #17324a;
}

section[data-testid="stSidebar"] > div {
    padding: .55rem .55rem .6rem;
}

section[data-testid="stSidebar"] .stButton > button {
    min-height: 40px;
    height: 40px;
    border-radius: 8px;
    border-color: transparent;
    color: #b4c5d5;
    font-size: .82rem;
    transition: all .16s ease;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #0d2539 !important;
    border-color: #214967 !important;
    transform: translateX(2px);
}

section[data-testid="stSidebar"] .stButton.nav-active > button {
    background: linear-gradient(135deg, #1352a2 0%, #0b3b79 100%) !important;
    border-color: #267ee0 !important;
    box-shadow: 0 7px 22px rgba(0,96,220,.20);
}

.top-header {
    min-height: 58px;
    padding: .05rem .15rem .3rem;
}

.title {
    font-size: 1.48rem;
    letter-spacing: -.035em;
}

.subtitle {
    font-size: .70rem;
}

.top-meta {
    gap: 7px;
}

.live-pill, .location-pill {
    backdrop-filter: blur(10px);
}

.search-wrap {
    margin-top: .1rem;
}

div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    background: #0a1724 !important;
    border-color: #213b53 !important;
}

div[data-testid="stButton"] > button {
    transition: all .16s ease;
}

div[data-testid="stButton"] > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 7px 18px rgba(0,100,220,.18);
}

/* The Folium iframe becomes a framed "satellite console". */
div[data-testid="stIFrame"] {
    border: 1px solid #17354d !important;
    border-radius: 0 0 12px 12px !important;
    overflow: hidden !important;
    box-shadow: 0 16px 35px rgba(0,0,0,.20);
    background: #06111b;
}

.map-card {
    border-color: #1b3c56;
    background: linear-gradient(145deg, #0a1a28, #07131f);
    border-radius: 12px 12px 0 0;
    padding: 9px 10px 8px;
}

.map-title {
    font-size: .95rem;
}

.map-sub {
    font-size: .60rem;
}

.layer-chip {
    color: #56e99a;
    border-color: rgba(53,223,136,.28);
    background: rgba(53,223,136,.08);
}

/* Right-side intelligence panel */
.dashboard-overview {
    height: 100%;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.overview-card {
    background:
        linear-gradient(145deg, rgba(12,29,45,.98), rgba(7,19,30,.98));
    border: 1px solid #1c3b53;
    border-radius: 11px;
    padding: 11px 12px;
    position: relative;
    overflow: hidden;
}

.overview-card:before {
    content: "";
    position: absolute;
    left: 0; top: 0; bottom: 0;
    width: 3px;
    background: #1688ff;
}

.overview-card.slide:before {
    background: #ff3f4f;
}

.overview-card .ov-title {
    display: flex;
    justify-content: space-between;
    align-items: center;
    color: #edf5fb;
    font-size: .77rem;
    font-weight: 850;
}

.overview-card .ov-status {
    padding: 3px 6px;
    border-radius: 5px;
    font-size: .48rem;
    font-weight: 900;
    background: rgba(140,160,178,.10);
    color: #9db0c0;
}

.overview-card .ov-value {
    margin-top: 9px;
    color: #f2f7fb;
    font-size: 1.02rem;
    font-weight: 850;
}

.overview-card .ov-label {
    margin-top: 2px;
    color: #6d879d;
    font-size: .52rem;
}

.overview-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 5px;
    margin-top: 8px;
}

.overview-kpi {
    background: #0a1a29;
    border: 1px solid #18354c;
    border-radius: 7px;
    padding: 7px;
}

.overview-kpi span {
    display: block;
    color: #647e94;
    font-size: .47rem;
    text-transform: uppercase;
    letter-spacing: .06em;
}

.overview-kpi b {
    display: block;
    margin-top: 3px;
    color: #e4edf4;
    font-size: .68rem;
}

.selected-card {
    background: linear-gradient(145deg, #0b1d2c, #081522);
    border: 1px solid #1c3b53;
    border-radius: 11px;
    padding: 10px 12px;
}

.selected-card .selected-title {
    color: #eef5fa;
    font-size: .76rem;
    font-weight: 850;
}

.selected-card .selected-location {
    color: #79a5ca;
    font-size: .61rem;
    margin-top: 3px;
}

/* Bottom command-center cards */
.command-grid {
    display: grid;
    grid-template-columns: 1.25fr .95fr 1fr;
    gap: 8px;
    margin-top: 8px;
}

.command-card {
    background: linear-gradient(145deg, #0a1928, #07131f);
    border: 1px solid #1a354b;
    border-radius: 11px;
    padding: 11px 12px;
    min-height: 142px;
}

.command-card.flood-card { border-top: 2px solid #1688ff; }
.command-card.slide-card { border-top: 2px solid #ff3f4f; }
.command-card.alert-card { border-top: 2px solid #f5c84c; }

.command-head {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 8px;
}

.command-title {
    color: #edf5fb;
    font-size: .78rem;
    font-weight: 850;
}

.command-meta {
    color: #627d94;
    font-size: .48rem;
}

.forecast-row {
    display: grid;
    grid-template-columns: 42px 1fr 48px;
    align-items: center;
    gap: 7px;
    margin-top: 9px;
}

.forecast-label, .forecast-level {
    font-size: .51rem;
    font-weight: 800;
    color: #8ca2b4;
}

.forecast-level { text-align: right; }

.forecast-track {
    height: 6px;
    border-radius: 8px;
    background: #102638;
    overflow: hidden;
}

.forecast-fill {
    height: 100%;
    border-radius: 8px;
    background: linear-gradient(90deg, #1688ff, #35a8ff);
}

.signal-row, .alert-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 10px;
    border-bottom: 1px solid #142d40;
    padding: 8px 0;
}

.signal-row:last-child, .alert-row:last-child { border-bottom: 0; }

.signal-name, .alert-name {
    color: #cbd8e3;
    font-size: .59rem;
    font-weight: 750;
}

.signal-sub, .alert-sub {
    color: #607b91;
    font-size: .48rem;
    margin-top: 2px;
}

.signal-value {
    font-size: .65rem;
    font-weight: 850;
}

.alert-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #35df88;
    flex: 0 0 auto;
}

.alert-dot.warn { background: #f5c84c; }
.alert-dot.high { background: #ff3f4f; }

.system-strip {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 7px;
    margin-top: 8px;
}

.system-chip {
    background: #091724;
    border: 1px solid #173149;
    border-radius: 8px;
    padding: 8px 9px;
}

.system-chip .chip-label {
    color: #5f7890;
    font-size: .45rem;
    text-transform: uppercase;
    letter-spacing: .08em;
}

.system-chip .chip-value {
    color: #cbd9e4;
    font-size: .58rem;
    font-weight: 750;
    margin-top: 3px;
}

.detail-card {
    background: linear-gradient(145deg, #0a1928, #07131f);
    border-color: #1b3b54;
    border-radius: 11px;
}

.detail-card.flood-detail { border-top: 2px solid #1688ff; }
.detail-card.slide-detail { border-top: 2px solid #ff3f4f; }

@media (max-width: 1050px) {
    section[data-testid="stSidebar"] {
        min-width: 220px;
        max-width: 220px;
    }
    .command-grid {
        grid-template-columns: 1fr;
    }
    .system-strip {
        grid-template-columns: 1fr 1fr;
    }
}



/* ============================================================
   DISASTERLENS AI — FINAL PRODUCT POLISH
   Visual-only layer. Existing backend/model/data logic preserved.
   ============================================================ */

.stApp {
    background:
        radial-gradient(circle at 55% -12%, rgba(24,74,117,.34), transparent 34%),
        radial-gradient(circle at 90% 45%, rgba(0,84,145,.08), transparent 28%),
        linear-gradient(180deg, #040b13 0%, #06121d 48%, #040a11 100%);
}

.main .block-container {
    max-width: 1500px;
    padding: .45rem .72rem .65rem;
}

.top-header {
    min-height: 62px;
    padding: .05rem .15rem .34rem;
    border-bottom: 1px solid rgba(34,76,108,.30);
    margin-bottom: .25rem;
}

.title {
    font-size: 1.46rem;
    font-weight: 900;
    letter-spacing: -.035em;
    text-shadow: 0 0 22px rgba(40,137,255,.08);
}

.subtitle {
    font-size: .68rem;
    color: #7590a7;
}

.top-meta { gap: 8px; }

.live-pill {
    border: 1px solid rgba(53,223,136,.36) !important;
    background: rgba(53,223,136,.075) !important;
    color: #45e794 !important;
    box-shadow: 0 0 18px rgba(53,223,136,.06);
}

.location-pill {
    border: 1px solid #1e405a !important;
    background: rgba(9,24,38,.88) !important;
    color: #b5c8d9 !important;
}

div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
    min-height: 42px;
    border-radius: 9px !important;
    background: linear-gradient(180deg,#101d2b,#0b1724) !important;
    border: 1px solid #21415b !important;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 8px 24px rgba(0,0,0,.12);
}

div[data-testid="stSelectbox"] [data-baseweb="select"] > div:hover {
    border-color: #2d6d9b !important;
}

div[data-testid="stButton"] > button {
    min-height: 42px;
    border-radius: 9px !important;
    border: 1px solid #2a4b65 !important;
    background: linear-gradient(135deg,#0f2d4a,#0b1d30) !important;
    color: #eaf4fb !important;
    font-weight: 800 !important;
    box-shadow: 0 8px 24px rgba(0,0,0,.14);
}

div[data-testid="stButton"] > button:hover {
    border-color: #2387e8 !important;
    background: linear-gradient(135deg,#124f8e,#0d3155) !important;
    box-shadow: 0 9px 28px rgba(20,119,225,.18);
}

.map-card {
    border: 1px solid #1e4967 !important;
    background: linear-gradient(145deg,#0a1d2d,#07131f) !important;
    box-shadow: 0 12px 28px rgba(0,0,0,.18);
}

.map-title { font-size: .97rem; font-weight: 900; }
.map-sub { color: #69869d; }

.layer-chip {
    padding: 5px 8px !important;
    border-radius: 999px !important;
    box-shadow: 0 0 16px rgba(53,223,136,.06);
}

div[data-testid="stIFrame"] {
    border-color: #1b4562 !important;
    box-shadow: 0 18px 42px rgba(0,0,0,.26) !important;
}

.dashboard-overview { gap: 7px; }

.overview-card,
.selected-card,
.command-card,
.system-chip {
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 9px 24px rgba(0,0,0,.12);
    transition: transform .16s ease, border-color .16s ease, box-shadow .16s ease;
}

.overview-card:hover,
.selected-card:hover,
.command-card:hover,
.system-chip:hover {
    transform: translateY(-1px);
    border-color: #2a5574;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.035), 0 13px 30px rgba(0,0,0,.18);
}

.overview-card .ov-value {
    font-size: 1.18rem;
    letter-spacing: -.02em;
}

.overview-card .ov-status {
    text-transform: uppercase;
    letter-spacing: .04em;
}

.command-grid {
    grid-template-columns: 1.16fr 1fr 1fr;
    gap: 9px;
    margin-top: 9px;
}

.command-card {
    min-height: 151px;
    padding: 12px 13px;
}

.command-title { font-size: .80rem; }
.command-meta { font-size: .50rem; }

.forecast-track {
    height: 7px;
    background: #0d2538;
    border: 1px solid #173b55;
}

.forecast-fill {
    background: linear-gradient(90deg,#1a8dff,#46b5ff) !important;
    box-shadow: 0 0 10px rgba(35,143,255,.20);
}

.signal-row, .alert-row { padding: 8px 0; }

.system-strip {
    gap: 8px;
    margin-top: 9px;
}

.system-chip {
    min-height: 50px;
    padding: 8px 10px;
}

.system-chip .chip-value { color: #d5e3ed; }

section[data-testid="stSidebar"] {
    min-width: 265px !important;
    max-width: 265px !important;
    border-right: 1px solid #17364e;
    box-shadow: 8px 0 28px rgba(0,0,0,.12);
}

section[data-testid="stSidebar"] .stButton > button {
    border: 1px solid transparent !important;
    background: transparent !important;
    min-height: 41px;
    border-radius: 9px !important;
    font-weight: 650 !important;
}

section[data-testid="stSidebar"] .stButton > button:hover {
    background: #0b253a !important;
    border-color: #1c4a68 !important;
}

section[data-testid="stSidebar"] .stButton.nav-active > button {
    background: linear-gradient(135deg,#1257ad,#0b3e7d) !important;
    border-color: #267fe0 !important;
    color: #fff !important;
    box-shadow: 0 8px 25px rgba(0,101,220,.20);
}

.status-box {
    box-shadow: inset 0 1px 0 rgba(255,255,255,.025), 0 12px 28px rgba(0,0,0,.16);
}

@media (max-width: 1150px) {
    section[data-testid="stSidebar"] {
        min-width: 235px !important;
        max-width: 235px !important;
    }
    .command-grid { grid-template-columns: 1fr 1fr; }
    .command-card.alert-card { grid-column: 1 / -1; }
}

@media (max-width: 850px) {
    .command-grid, .system-strip { grid-template-columns: 1fr; }
    .command-card.alert-card { grid-column: auto; }
    .title { font-size: 1.18rem; }
}


/* ============================================================
   ANALYTICS / WEATHER / ALERTS — FINAL UI REFINEMENT
   Presentation-only styles. Existing data and logic are preserved.
   ============================================================ */

.intel-hero {
    display:flex;
    align-items:flex-end;
    justify-content:space-between;
    gap:18px;
    padding:15px 17px;
    margin-bottom:9px;
    border:1px solid #1b405b;
    border-radius:13px;
    background:
        radial-gradient(circle at 85% 20%, rgba(35,132,224,.14), transparent 28%),
        linear-gradient(145deg,#0b1b2a,#07131f);
    box-shadow:inset 0 1px 0 rgba(255,255,255,.025),0 10px 28px rgba(0,0,0,.14);
}
.intel-kicker {
    color:#5f86a5;
    font-size:.52rem;
    font-weight:900;
    letter-spacing:.14em;
    text-transform:uppercase;
    margin-bottom:4px;
}
.intel-title {
    color:#f3f8fc;
    font-size:1.15rem;
    font-weight:900;
    letter-spacing:-.025em;
}
.intel-sub {
    color:#7892a8;
    font-size:.61rem;
    margin-top:3px;
}
.intel-live {
    white-space:nowrap;
    padding:6px 9px;
    border-radius:999px;
    color:#45e794;
    background:rgba(53,223,136,.07);
    border:1px solid rgba(53,223,136,.28);
    font-size:.55rem;
    font-weight:900;
}

.panel-section-title {
    color:#607e96;
    font-size:.55rem;
    font-weight:900;
    letter-spacing:.12em;
    text-transform:uppercase;
    margin:8px 0 5px;
}

.analytics-kpis {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:8px;
    margin:8px 0;
}
.analytics-kpi {
    position:relative;
    overflow:hidden;
    background:linear-gradient(145deg,#0b1c2b,#07131f);
    border:1px solid #1b3a52;
    border-radius:11px;
    padding:10px 11px;
}
.analytics-kpi:before {
    content:"";
    position:absolute;
    left:0; top:0; bottom:0;
    width:3px;
    background:#1688ff;
}
.analytics-kpi.slide:before { background:#ff3f4f; }
.analytics-kpi .k-label {
    color:#648098;
    font-size:.49rem;
    text-transform:uppercase;
    letter-spacing:.07em;
    font-weight:850;
}
.analytics-kpi .k-value {
    color:#edf5fa;
    font-size:1.18rem;
    font-weight:900;
    margin-top:5px;
}
.analytics-kpi .k-sub {
    color:#60798f;
    font-size:.50rem;
    margin-top:2px;
}
.analytics-kpi .k-value.low { color:#35df88; }
.analytics-kpi .k-value.medium { color:#f5c84c; }
.analytics-kpi .k-value.high { color:#ff4b59; }

.analytics-panel {
    background:linear-gradient(145deg,#0a1928,#07131f);
    border:1px solid #1a374d;
    border-radius:12px;
    padding:11px 12px;
    box-shadow:inset 0 1px 0 rgba(255,255,255,.02);
}
.analytics-panel-head {
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    margin-bottom:8px;
}
.analytics-panel-title {
    color:#eaf3f9;
    font-size:.76rem;
    font-weight:900;
}
.analytics-panel-meta {
    color:#5f7b92;
    font-size:.49rem;
}
.bar-row {
    display:grid;
    grid-template-columns:105px 1fr 52px;
    align-items:center;
    gap:8px;
    margin:10px 0;
}
.bar-label {
    color:#b8c9d6;
    font-size:.56rem;
    font-weight:750;
}
.bar-track {
    height:9px;
    background:#0c2437;
    border:1px solid #173b55;
    border-radius:999px;
    overflow:hidden;
}
.bar-fill {
    height:100%;
    border-radius:999px;
    background:linear-gradient(90deg,#147dff,#42b4ff);
    box-shadow:0 0 12px rgba(35,143,255,.17);
}
.bar-fill.slide {
    background:linear-gradient(90deg,#d93655,#ff6974);
}
.bar-value {
    text-align:right;
    color:#e5eef4;
    font-size:.56rem;
    font-weight:850;
}
.forecast-grid {
    display:grid;
    grid-template-columns:repeat(3,1fr);
    gap:8px;
    margin-top:8px;
}
.forecast-card {
    background:#091a29;
    border:1px solid #19374e;
    border-radius:10px;
    padding:10px;
}
.forecast-card .fc-time {
    color:#607d95;
    font-size:.48rem;
    text-transform:uppercase;
    letter-spacing:.08em;
    font-weight:850;
}
.forecast-card .fc-score {
    color:#edf5fb;
    font-size:1.05rem;
    font-weight:900;
    margin-top:4px;
}
.forecast-card .fc-level {
    font-size:.51rem;
    font-weight:900;
    margin-top:3px;
}
.signal-grid {
    display:grid;
    grid-template-columns:1fr 1fr;
    gap:8px;
    margin-top:8px;
}
.signal-card {
    background:#091a29;
    border:1px solid #19374e;
    border-radius:10px;
    padding:10px;
}
.signal-card .s-label {
    color:#67839a;
    font-size:.48rem;
    text-transform:uppercase;
    letter-spacing:.07em;
    font-weight:850;
}
.signal-card .s-value {
    color:#edf5fb;
    font-size:1rem;
    font-weight:900;
    margin-top:4px;
}
.signal-card .s-sub {
    color:#617a90;
    font-size:.49rem;
    margin-top:2px;
}

.source-strip {
    display:grid;
    grid-template-columns:repeat(4,1fr);
    gap:7px;
    margin-top:8px;
}
.source-chip {
    background:#091824;
    border:1px solid #17334a;
    border-radius:9px;
    padding:8px 9px;
}
.source-chip b {
    display:block;
    color:#d8e5ee;
    font-size:.57rem;
}
.source-chip span {
    display:block;
    color:#607a90;
    font-size:.47rem;
    margin-top:2px;
}

.weather-current {
    display:grid;
    grid-template-columns:repeat(5,1fr);
    gap:8px;
    margin:9px 0;
}
.weather-card {
    background:linear-gradient(145deg,#0b1c2b,#07131f);
    border:1px solid #1a394f;
    border-radius:11px;
    padding:11px;
    min-height:76px;
}
.weather-card .w-label {
    color:#668198;
    font-size:.50rem;
    text-transform:uppercase;
    letter-spacing:.07em;
    font-weight:850;
}
.weather-card .w-icon {
    float:right;
    font-size:.85rem;
    opacity:.9;
}
.weather-card .w-value {
    color:#f1f7fb;
    font-size:1.16rem;
    font-weight:900;
    margin-top:8px;
}
.weather-card .w-sub {
    color:#5f788f;
    font-size:.48rem;
    margin-top:2px;
}
.weather-chart-panel {
    background:linear-gradient(145deg,#0a1928,#07131f);
    border:1px solid #1a374d;
    border-radius:12px;
    padding:11px 12px;
    margin-top:8px;
}
.weather-chart-head {
    display:flex;
    justify-content:space-between;
    align-items:center;
    gap:10px;
    margin-bottom:5px;
}
.weather-chart-title {
    color:#eaf3f9;
    font-size:.75rem;
    font-weight:900;
}
.weather-chart-meta {
    color:#607b92;
    font-size:.49rem;
}
.weather-svg {
    width:100%;
    height:175px;
    display:block;
}
.weather-days {
    display:grid;
    grid-template-columns:repeat(7,1fr);
    gap:6px;
    margin-top:8px;
}
.weather-day {
    background:#091a29;
    border:1px solid #19364d;
    border-radius:9px;
    padding:8px 6px;
    text-align:center;
}
.weather-day .day {
    color:#6b879d;
    font-size:.48rem;
    font-weight:850;
}
.weather-day .cond {
    color:#cbd9e3;
    font-size:.55rem;
    margin:5px 0;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
}
.weather-day .temp {
    color:#eef5f9;
    font-size:.66rem;
    font-weight:850;
}
.weather-day .rain {
    color:#4caeff;
    font-size:.48rem;
    margin-top:3px;
}
.weather-note {
    color:#5f778c;
    font-size:.51rem;
    margin-top:7px;
}

.alert-summary {
    display:grid;
    grid-template-columns:1.1fr 1fr 1fr 1fr;
    gap:8px;
    margin:8px 0;
}
.alert-summary-card {
    background:linear-gradient(145deg,#0b1c2b,#07131f);
    border:1px solid #1a374d;
    border-radius:10px;
    padding:10px 11px;
}
.alert-summary-card .as-label {
    color:#648098;
    font-size:.48rem;
    text-transform:uppercase;
    letter-spacing:.07em;
    font-weight:850;
}
.alert-summary-card .as-value {
    color:#edf5fa;
    font-size:1.12rem;
    font-weight:900;
    margin-top:4px;
}
.alert-summary-card.high .as-value { color:#ff4c59; }
.alert-summary-card.medium .as-value { color:#f5c84c; }
.alert-summary-card.low .as-value { color:#35df88; }

.alert-list {
    background:linear-gradient(145deg,#0a1928,#07131f);
    border:1px solid #1a374d;
    border-radius:12px;
    padding:8px 12px;
}
.alert-list-head {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:4px 0 7px;
    border-bottom:1px solid #173248;
}
.alert-list-title {
    color:#eaf3f9;
    font-size:.76rem;
    font-weight:900;
}
.alert-list-meta {
    color:#607b92;
    font-size:.49rem;
}
.alert-row-new {
    display:grid;
    grid-template-columns:8px 74px 1fr auto;
    gap:10px;
    align-items:center;
    padding:10px 2px;
    border-bottom:1px solid #142d40;
}
.alert-row-new:last-child { border-bottom:0; }
.alert-sev-dot {
    width:7px;
    height:7px;
    border-radius:50%;
}
.alert-sev-dot.high { background:#ff3f4f; box-shadow:0 0 9px rgba(255,63,79,.35); }
.alert-sev-dot.medium { background:#f5c84c; }
.alert-sev-dot.low { background:#35df88; }
.alert-severity {
    font-size:.50rem;
    font-weight:900;
    letter-spacing:.06em;
}
.alert-severity.high { color:#ff6570; }
.alert-severity.medium { color:#f5d05e; }
.alert-severity.low { color:#45e794; }
.alert-hazard {
    color:#d9e5ed;
    font-size:.61rem;
    font-weight:800;
}
.alert-message {
    color:#637f95;
    font-size:.50rem;
    margin-top:2px;
}
.alert-time {
    color:#70889c;
    font-size:.49rem;
    text-align:right;
    white-space:nowrap;
}
.alert-disclaimer {
    margin-top:8px;
    padding:9px 11px;
    border:1px solid #234966;
    background:rgba(28,103,165,.10);
    border-radius:9px;
    color:#75a7d0;
    font-size:.52rem;
    line-height:1.45;
}

@media (max-width: 1050px) {
    .analytics-kpis, .weather-current { grid-template-columns:1fr 1fr; }
    .weather-days { grid-template-columns:repeat(4,1fr); }
    .alert-summary { grid-template-columns:1fr 1fr; }
}
@media (max-width: 700px) {
    .forecast-grid, .signal-grid, .source-strip { grid-template-columns:1fr; }
    .weather-days { grid-template-columns:1fr 1fr; }
    .alert-row-new { grid-template-columns:8px 68px 1fr; }
    .alert-time { grid-column:3; text-align:left; }
}

</style>
"""
)


# ============================================================
# SESSION STATE
# ============================================================

defaults = {
    "page": "Dashboard",
    "selected_location": "",
    "location_name": "Chandigarh, India",
    "latitude": 30.7333,
    "longitude": 76.7794,
    "flood_result": None,
    "landslide_result": None,
    "last_error": None,
    "last_analyzed_key": None,
    "running": False,
    "weather_data": None,
    "report_timestamp": None,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ============================================================
# HELPERS
# ============================================================

def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def clean_level(value):
    if value is None:
        return "UNKNOWN"
    return str(value).upper().strip()


def risk_class(level):
    level = clean_level(level)
    if level == "HIGH":
        return "risk-high"
    if level == "MEDIUM":
        return "risk-medium"
    if level == "LOW":
        return "risk-low"
    return "risk-unknown"


def risk_color(level, default="#8ca0b2"):
    level = clean_level(level)
    if level == "HIGH":
        return "#ff3f4f"
    if level == "MEDIUM":
        return "#f5c84c"
    if level == "LOW":
        return "#35df88"
    return default


def short_date(value):
    if not value:
        return "—"
    text_value = str(value)
    return text_value.replace("T", " ")[:19]


def safe_text(value, default="—"):
    if value is None or value == "":
        return default
    return html.escape(str(value))


WEATHER_CODE_TEXT = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Thunderstorm with heavy hail",
}


@st.cache_data(ttl=600, show_spinner=False)
def fetch_weather_data(lat, lon):
    """Fetch live Open-Meteo weather for the selected coordinates."""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": float(lat),
        "longitude": float(lon),
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "precipitation",
            "rain",
            "wind_speed_10m",
            "weather_code",
        ]),
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
        ]),
        "forecast_days": 7,
        "timezone": "auto",
    }

    response = requests.get(url, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def weather_text(code):
    try:
        return WEATHER_CODE_TEXT.get(int(code), "Unknown")
    except (TypeError, ValueError):
        return "Unknown"


def current_weather_values(data):
    current = data.get("current", {}) if isinstance(data, dict) else {}
    return {
        "temperature": safe_float(current.get("temperature_2m")),
        "humidity": safe_float(current.get("relative_humidity_2m")),
        "precipitation": safe_float(current.get("precipitation")),
        "rain": safe_float(current.get("rain")),
        "wind": safe_float(current.get("wind_speed_10m")),
        "code": current.get("weather_code"),
    }


def weather_dataframe(data):
    daily = data.get("daily", {}) if isinstance(data, dict) else {}
    dates = daily.get("time", [])
    return pd.DataFrame({
        "Date": pd.to_datetime(dates),
        "Condition": [weather_text(x) for x in daily.get("weather_code", [])],
        "Max °C": daily.get("temperature_2m_max", []),
        "Min °C": daily.get("temperature_2m_min", []),
        "Rain mm": daily.get("precipitation_sum", []),
        "Rain probability %": daily.get("precipitation_probability_max", []),
        "Max wind km/h": daily.get("wind_speed_10m_max", []),
    })


def build_alerts():
    """Build transparent, local dashboard indicators from current results.

    These are application-level indicators, not official government alerts.
    """
    alerts = []

    if flood_ok:
        if flood_level == "HIGH":
            alerts.append(("HIGH", "Flood", "Current flood analysis is HIGH."))
        elif flood_level == "MEDIUM":
            alerts.append(("MEDIUM", "Flood", "Current flood analysis is MEDIUM."))
        else:
            alerts.append(("LOW", "Flood", f"Current detected coverage is {flood_coverage:.2f}%."))

        for period, label in [("24h", "24-hour"), ("48h", "48-hour"), ("72h", "72-hour")]:
            item = ff.get(period, {}) if isinstance(ff, dict) else {}
            lvl = clean_level(item.get("level", "UNKNOWN"))
            score = safe_float(item.get("score"))
            if lvl in {"HIGH", "MEDIUM"}:
                alerts.append((lvl, "Future Flood Risk", f"{label} risk is {lvl} with score {score:.2f}."))

    if slide_ok:
        if slide_level == "HIGH":
            alerts.append(("HIGH", "Landslide", "Current landslide analysis is HIGH."))
        elif slide_level == "MEDIUM":
            alerts.append(("MEDIUM", "Landslide", "Current landslide analysis is MEDIUM."))
        else:
            alerts.append(("LOW", "Landslide", f"Detected coverage is {slide_coverage:.2f}%."))

    weather = st.session_state.get("weather_data")
    if weather:
        cur = current_weather_values(weather)
        daily = weather_dataframe(weather)
        if not daily.empty:
            max_rain = safe_float(daily["Rain mm"].max())
            max_prob = safe_float(daily["Rain probability %"].max())
            max_wind = safe_float(daily["Max wind km/h"].max())
            if max_rain >= 50 or (max_prob >= 80 and max_rain >= 20):
                alerts.append(("MEDIUM", "Weather", f"Forecast indicates potentially heavy rainfall: up to {max_rain:.1f} mm/day."))
            if max_wind >= 60:
                alerts.append(("MEDIUM", "Weather", f"Forecast maximum wind reaches {max_wind:.1f} km/h."))
            if cur["code"] in {95, 96, 99}:
                alerts.append(("MEDIUM", "Weather", "Current weather code indicates a thunderstorm."))

    return alerts


def make_report_data():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = []
    rows.append({"Section": "Location", "Metric": "Location", "Value": st.session_state.location_name})
    rows.append({"Section": "Location", "Metric": "Latitude", "Value": f"{lat:.6f}"})
    rows.append({"Section": "Location", "Metric": "Longitude", "Value": f"{lon:.6f}"})
    rows.append({"Section": "Report", "Metric": "Generated", "Value": now})

    rows.extend([
        {"Section": "Flood", "Metric": "Risk", "Value": flood_level},
        {"Section": "Flood", "Metric": "Coverage %", "Value": f"{flood_coverage:.2f}"},
        {"Section": "Flood", "Metric": "Model Confidence %", "Value": f"{safe_float(fc.get('model_confidence')):.2f}"},
        {"Section": "Flood", "Metric": "Sentinel-1 Date", "Value": short_date(fc.get("satellite_image_date"))},
        {"Section": "Flood", "Metric": "24h Rainfall mm", "Value": f"{safe_float(fw.get('next_24h_rainfall_mm')):.1f}"},
    ])

    for period in ["24h", "48h", "72h"]:
        item = ff.get(period, {}) if isinstance(ff, dict) else {}
        rows.append({
            "Section": "Flood Future Risk",
            "Metric": period,
            "Value": f"{safe_float(item.get('score')):.2f} ({clean_level(item.get('level', 'UNKNOWN'))})",
        })

    rows.extend([
        {"Section": "Landslide", "Metric": "Risk", "Value": slide_level},
        {"Section": "Landslide", "Metric": "Coverage %", "Value": f"{slide_coverage:.2f}"},
        {"Section": "Landslide", "Metric": "Mean Probability", "Value": f"{safe_float(landslide.get('mean_probability', 0) if isinstance(landslide, dict) else 0):.4f}"},
        {"Section": "Landslide", "Metric": "Max Probability", "Value": f"{safe_float(landslide.get('max_probability', 0) if isinstance(landslide, dict) else 0):.4f}"},
        {"Section": "Landslide", "Metric": "Sentinel-2 Date", "Value": short_date(landslide.get('acquisition_date') if isinstance(landslide, dict) else None)},
    ])

    weather = st.session_state.get("weather_data")
    if weather:
        cur = current_weather_values(weather)
        rows.extend([
            {"Section": "Weather", "Metric": "Current Temperature °C", "Value": f"{cur['temperature']:.1f}"},
            {"Section": "Weather", "Metric": "Humidity %", "Value": f"{cur['humidity']:.0f}"},
            {"Section": "Weather", "Metric": "Wind km/h", "Value": f"{cur['wind']:.1f}"},
            {"Section": "Weather", "Metric": "Condition", "Value": weather_text(cur['code'])},
        ])

    return pd.DataFrame(rows)


def make_report_html(report_df):
    rows_html = "".join(
        f"<tr><td>{html.escape(str(row['Metric']))}</td><td>{html.escape(str(row['Value']))}</td></tr>"
        for _, row in report_df.iterrows()
    )
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>DisasterLens AI Report</title>
<style>body{{font-family:Arial,sans-serif;margin:35px;color:#172333}}h1{{margin-bottom:4px}}.sub{{color:#667789}}table{{width:100%;border-collapse:collapse;margin-top:20px}}td{{padding:8px;border-bottom:1px solid #ddd}}td:first-child{{font-weight:700;width:35%}}.section{{margin-top:22px;font-size:18px;font-weight:700}}</style></head>
<body><h1>DisasterLens AI — Analysis Report</h1>
<div class='sub'>{html.escape(st.session_state.location_name)} • Generated {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
<table>{rows_html}</table>
<p style='margin-top:28px;color:#68798a;font-size:12px'>This report summarizes the current application analysis. Risk indicators are model/application outputs and are not a substitute for official emergency warnings.</p>
</body></html>"""


def make_report_pdf(report_df):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=32, leftMargin=32, topMargin=32, bottomMargin=32)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("DisasterLens AI — Analysis Report", styles["Title"]),
            Paragraph(f"{html.escape(st.session_state.location_name)} • {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles["Normal"]),
            Spacer(1, 14),
        ]
        data = [["Metric", "Value"]] + [[str(r["Metric"]), str(r["Value"])] for _, r in report_df.iterrows()]
        table = Table(data, colWidths=[180, 330])
        table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#173b5e")),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#cfd8e0")),
            ("VALIGN", (0,0), (-1,-1), "TOP"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("BOTTOMPADDING", (0,0), (-1,0), 7),
            ("TOPPADDING", (0,0), (-1,0), 7),
        ]))
        story.append(table)
        story.append(Spacer(1, 14))
        story.append(Paragraph("Application risk indicators are not official emergency warnings.", styles["Normal"]))
        doc.build(story)
        return buffer.getvalue()
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def geocode_location(query):
    geolocator = Nominatim(
        user_agent="DisasterLens-AI"
    )
    location = geolocator.geocode(
        query,
        language="en",
        addressdetails=True,
        timeout=12,
    )
    if location is None:
        return None

    return {
        "latitude": float(location.latitude),
        "longitude": float(location.longitude),
        "display_name": location.address,
    }


def parse_location(query):
    query = query.strip()

    # Coordinates are supported directly.
    parts = query.split(",")
    if len(parts) == 2:
        try:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())

            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "display_name": (
                        f"Selected Location "
                        f"({lat:.4f}, {lon:.4f})"
                    ),
                }
        except ValueError:
            pass

    return geocode_location(query)


# ============================================================
# LOCATION SUGGESTIONS
# ============================================================
#
# These are convenience suggestions only. They are NOT a whitelist.
# accept_new_options=True means users can still type and analyze
# villages, towns, districts, countries, or coordinates that are
# not present here.
#
LOCATION_SUGGESTIONS = [
    # Indian states
    "Andhra Pradesh",
    "Arunachal Pradesh",
    "Assam",
    "Bihar",
    "Chhattisgarh",
    "Goa",
    "Gujarat",
    "Haryana",
    "Himachal Pradesh",
    "Jharkhand",
    "Karnataka",
    "Kerala",
    "Madhya Pradesh",
    "Maharashtra",
    "Manipur",
    "Meghalaya",
    "Mizoram",
    "Nagaland",
    "Odisha",
    "Punjab",
    "Rajasthan",
    "Sikkim",
    "Tamil Nadu",
    "Telangana",
    "Tripura",
    "Uttar Pradesh",
    "Uttarakhand",
    "West Bengal",

    # Union Territories
    "Andaman and Nicobar Islands",
    "Chandigarh",
    "Dadra and Nagar Haveli and Daman and Diu",
    "Delhi",
    "Jammu and Kashmir",
    "Ladakh",
    "Lakshadweep",
    "Puducherry",

    # Major Indian cities / regional centres
    "Ahmedabad, Gujarat",
    "Amritsar, Punjab",
    "Bengaluru, Karnataka",
    "Bhopal, Madhya Pradesh",
    "Bhubaneswar, Odisha",
    "Chandigarh, India",
    "Chennai, Tamil Nadu",
    "Dehradun, Uttarakhand",
    "Delhi, India",
    "Dharamshala, Himachal Pradesh",
    "Dispur, Assam",
    "Gandhinagar, Gujarat",
    "Gangtok, Sikkim",
    "Gurugram, Haryana",
    "Guwahati, Assam",
    "Hyderabad, Telangana",
    "Imphal, Manipur",
    "Indore, Madhya Pradesh",
    "Jaipur, Rajasthan",
    "Jammu, Jammu and Kashmir",
    "Kochi, Kerala",
    "Kolkata, West Bengal",
    "Lucknow, Uttar Pradesh",
    "Ludhiana, Punjab",
    "Mumbai, Maharashtra",
    "Nagpur, Maharashtra",
    "New Delhi, India",
    "Panaji, Goa",
    "Patna, Bihar",
    "Port Blair, Andaman and Nicobar Islands",
    "Pune, Maharashtra",
    "Raipur, Chhattisgarh",
    "Ranchi, Jharkhand",
    "Shillong, Meghalaya",
    "Shimla, Himachal Pradesh",
    "Srinagar, Jammu and Kashmir",
    "Surat, Gujarat",
    "Thiruvananthapuram, Kerala",
    "Udaipur, Rajasthan",
    "Varanasi, Uttar Pradesh",
    "Vijayawada, Andhra Pradesh",
    "Visakhapatnam, Andhra Pradesh",

    # Nearby / useful international locations
    "Kathmandu, Nepal",
    "Pokhara, Nepal",
]

LOCATION_SUGGESTIONS = list(dict.fromkeys(LOCATION_SUGGESTIONS))


def process_location_query(query, rerun_after=True):
    """Resolve a location and run the existing analysis pipeline.

    This function intentionally reuses the existing backend/model
    functions. It only handles the location-search interaction.
    """
    query = str(query or "").strip()

    if not query:
        st.error("Please enter a location.")
        return False

    with st.spinner("Locating the selected area..."):
        location = parse_location(query)

    if location is None:
        st.error(
            "Location not found. Try a city, district, country or coordinates."
        )
        return False

    st.session_state.selected_location = query
    st.session_state.location_name = location["display_name"]
    st.session_state.latitude = location["latitude"]
    st.session_state.longitude = location["longitude"]

    # Clear previous result so the user sees that a new analysis
    # is being performed.
    st.session_state.last_analyzed_key = None

    if page == "Dashboard":
        message = "Running Flood + Landslide analysis..."
    elif page == "Flood":
        message = "Running live Flood V3 analysis..."
    else:
        message = "Running live Landslide V5 analysis..."

    with st.spinner(message):
        run_requested_analysis()

    if rerun_after:
        st.rerun()

    return True


def handle_location_selector_change():
    """Called when the searchable location selector is confirmed.

    Streamlit's searchable selectbox supports both:
      - selecting a suggested location
      - typing a completely new location and pressing Enter
    """
    selected = st.session_state.get("location_selector", "")
    if selected:
        process_location_query(selected, rerun_after=False)


def analysis_key(lat, lon):
    return hashlib.md5(
        f"{lat:.6f},{lon:.6f}".encode()
    ).hexdigest()


def run_requested_analysis():
    lat = st.session_state.latitude
    lon = st.session_state.longitude
    page = st.session_state.page

    st.session_state.last_error = None
    st.session_state.running = True

    # --------------------------------------------------------
    # Dashboard = both hazards
    # --------------------------------------------------------
    if page == "Dashboard":
        try:
            st.session_state.flood_result = analyze_future_flood(
                lat,
                lon
            )
        except Exception as exc:
            st.session_state.flood_result = {
                "success": False,
                "error": str(exc),
            }

        try:
            st.session_state.landslide_result = analyze_landslide(
                lat,
                lon
            )
        except Exception as exc:
            st.session_state.landslide_result = {
                "success": False,
                "error": str(exc),
                "risk_level": "UNKNOWN",
                "risk": "UNKNOWN",
                "coverage": 0.0,
                "landslide_coverage_percent": 0.0,
                "mean_probability": 0.0,
                "max_probability": 0.0,
                "landslide_pixels": 0,
                "total_pixels": 16384,
                "mask": [[0] * 128 for _ in range(128)],
            }

    # --------------------------------------------------------
    # Flood page
    # --------------------------------------------------------
    elif page == "Flood":
        try:
            st.session_state.flood_result = analyze_future_flood(
                lat,
                lon
            )
        except Exception as exc:
            st.session_state.flood_result = {
                "success": False,
                "error": str(exc),
            }

    # --------------------------------------------------------
    # Landslide page
    # --------------------------------------------------------
    elif page == "Landslide":
        try:
            st.session_state.landslide_result = analyze_landslide(
                lat,
                lon
            )
        except Exception as exc:
            st.session_state.landslide_result = {
                "success": False,
                "error": str(exc),
                "risk_level": "UNKNOWN",
                "risk": "UNKNOWN",
                "coverage": 0.0,
                "landslide_coverage_percent": 0.0,
                "mean_probability": 0.0,
                "max_probability": 0.0,
                "landslide_pixels": 0,
                "total_pixels": 16384,
                "mask": [[0] * 128 for _ in range(128)],
            }

    st.session_state.last_analyzed_key = analysis_key(
        lat,
        lon
    )
    st.session_state.running = False


def select_page(page):
    st.session_state.page = page
    st.session_state.last_error = None


# ============================================================
# SIDEBAR
# ============================================================

with st.sidebar:

    st.html(
        """
        <div class="brand-box">
            <div class="brand-row">
                <div class="brand-logo">🌍</div>
                <div>
                    <div class="brand-name">DisasterLens AI</div>
                    <div class="brand-sub">
                        Multi-Hazard Satellite Intelligence<br>
                        Early Warning &amp; Risk Monitoring
                    </div>
                </div>
            </div>
        </div>
        """
    )

    st.html('<div class="nav-label">MONITORING</div>')

    if st.button(
        "◉  Dashboard",
        key="nav_dashboard",
        use_container_width=True,
    ):
        select_page("Dashboard")
        st.rerun()

    if st.button(
        "🌊  Flood Intelligence",
        key="nav_flood",
        use_container_width=True,
    ):
        select_page("Flood")
        st.rerun()

    if st.button(
        "⛰️  Landslide Intelligence",
        key="nav_landslide",
        use_container_width=True,
    ):
        select_page("Landslide")
        st.rerun()

    st.html('<div class="nav-label">SYSTEM</div>')

    if st.button(
        "📊  Analytics",
        key="nav_analytics",
        use_container_width=True,
    ):
        select_page("Analytics")
        st.rerun()

    if st.button(
        "🌦️  Weather",
        key="nav_weather",
        use_container_width=True,
    ):
        select_page("Weather")
        st.rerun()

    if st.button(
        "🔔  Alerts",
        key="nav_alerts",
        use_container_width=True,
    ):
        select_page("Alerts")
        st.rerun()

    if st.button(
        "📄  Reports",
        key="nav_reports",
        use_container_width=True,
    ):
        select_page("Reports")
        st.rerun()

    st.html(
        """
        <div class="status-box">
            <div class="status-head">● SYSTEM OPERATIONAL</div>
            <div class="status-line">Flood Model: <b>U-Net V3</b></div>
            <div class="status-line">Landslide Model: <b>U-Net V5</b></div>
            <div class="status-line">Flood Satellite: <b>Sentinel-1 SAR</b></div>
            <div class="status-line">Landslide Satellite: <b>Sentinel-2</b></div>
            <div class="status-line">Geospatial: <b>Google Earth Engine</b></div>
        </div>
        """
    )


# ============================================================
# PAGE HEADER
# ============================================================

page = st.session_state.page

titles = {
    "Dashboard": (
        "AI-Powered Multi-Hazard Disaster Intelligence",
        "Satellite intelligence for flood & landslide detection and early-warning analysis",
    ),
    "Flood": (
        "AI-Powered Flood Detection & Prediction",
        "Sentinel-1 SAR intelligence for live flood segmentation and future risk",
    ),
    "Landslide": (
        "AI-Powered Landslide Detection",
        "Sentinel-2 + DEM intelligence for live landslide segmentation and risk",
    ),
    "Analytics": (
        "Disaster Intelligence Analytics",
        "Interactive snapshot of the latest Flood and Landslide analysis",
    ),
    "Weather": (
        "Live Weather Intelligence",
        "Current conditions and seven-day forecast for the selected location",
    ),
    "Alerts": (
        "Hazard & Weather Alerts",
        "Application-level indicators derived from the latest available analysis",
    ),
    "Reports": (
        "Disaster Analysis Reports",
        "Review, export and download the current DisasterLens AI analysis",
    ),
}

title_text, subtitle_text = titles[page]

st.html(
    f"""
    <div class="top-header">
        <div>
            <div class="title">{title_text}</div>
            <div class="subtitle">{subtitle_text}</div>
        </div>
        <div class="top-meta">
            <div class="live-pill">● LIVE SYSTEM</div>
            <div class="location-pill">📍 {safe_text(st.session_state.location_name)}</div>
            <div class="location-pill">◷ {datetime.now().strftime("%d %b %Y · %I:%M %p")}</div>
        </div>
    </div>
    """
)


# ============================================================
# LOCATION SEARCH
# ============================================================
#
# Native searchable suggestions:
# - Type a city/state/etc. to filter suggestions.
# - Press Enter to select a suggestion or confirm a new location.
# - New locations are accepted even when they are not in the list.
# - The existing backend/model analysis flow is reused unchanged.
# ============================================================

search_col, button_col = st.columns(
    [5.8, 0.9],
    gap="small"
)

with search_col:
    location_options = list(LOCATION_SUGGESTIONS)

    current_location = str(
        st.session_state.get("selected_location", "") or ""
    ).strip()

    if current_location and current_location not in location_options:
        location_options.insert(0, current_location)

    selected_location_input = st.selectbox(
        "Location",
        options=location_options,
        index=(
            location_options.index(current_location)
            if current_location in location_options
            else None
        ),
        placeholder="Search city, district, village or enter coordinates...",
        label_visibility="collapsed",
        key="location_selector",
        accept_new_options=True,
        filter_mode="contains",
        on_change=handle_location_selector_change,
    )

with button_col:
    submitted = st.button(
        "🔍 Analyze",
        use_container_width=True,
        key="analyze_location_button",
    )

if submitted:
    process_location_query(
        selected_location_input,
        rerun_after=True,
    )


# ============================================================
# RESULT ACCESSORS
# ============================================================

flood = st.session_state.flood_result
landslide = st.session_state.landslide_result

flood_ok = bool(
    isinstance(flood, dict)
    and flood.get("success", False)
)

slide_ok = bool(
    isinstance(landslide, dict)
    and landslide.get("success", False)
)


def flood_current():
    if not flood_ok:
        return {}
    return flood.get("current_condition", {})


def flood_weather():
    if not flood_ok:
        return {}
    return flood.get("forecast_weather", {})


def flood_future():
    if not flood_ok:
        return {}
    return flood.get("future_flood_risk", {})


fc = flood_current()
fw = flood_weather()
ff = flood_future()

flood_level = clean_level(fc.get("alert_level", "UNKNOWN"))
slide_level = clean_level(
    landslide.get("risk_level", landslide.get("risk", "UNKNOWN"))
    if isinstance(landslide, dict)
    else "UNKNOWN"
)

flood_coverage = safe_float(
    fc.get("flood_coverage_percentage", 0)
)

slide_coverage = safe_float(
    landslide.get(
        "landslide_coverage_percent",
        landslide.get("coverage", 0)
    )
    if isinstance(landslide, dict)
    else 0
)

mean_probability = safe_float(
    landslide.get("mean_probability", 0) if isinstance(landslide, dict) else 0
)

max_probability = safe_float(
    landslide.get("max_probability", 0) if isinstance(landslide, dict) else 0
)


# ============================================================
# MAP HELPERS
# ============================================================

def add_flood_visual(
    m,
    lat,
    lon,
    coverage,
    level,
    show_blue=True,
    layer_name="Flood Affected Area",
):
    """
    The current Flood API returns coverage/risk but does not
    expose its pixel mask. Therefore the frontend uses a
    clearly styled blue risk footprint rather than pretending
    it is a pixel-perfect U-Net georeferenced mask.
    """

    group = folium.FeatureGroup(
        name=layer_name,
        show=show_blue,
    )

    # Outer analysis footprint
    folium.Circle(
        [lat, lon],
        radius=11500,
        color="#ffffff",
        weight=1,
        fill=False,
        opacity=.48,
    ).add_to(group)

    # Blue flood visualization.
    # Size scales gently with actual detected coverage.
    if level == "HIGH":
        radius = 4800 + min(coverage * 45, 3800)
        opacity = .29
    elif level == "MEDIUM":
        radius = 4000 + min(coverage * 38, 3000)
        opacity = .24
    else:
        radius = 3000 + min(coverage * 30, 2200)
        opacity = .18

    # Layer 1: soft blue water footprint
    folium.Circle(
        [lat, lon],
        radius=radius,
        color="#1688ff",
        weight=1,
        fill=True,
        fill_color="#1688ff",
        fill_opacity=opacity * .42,
        opacity=.75,
        tooltip=f"Flood affected area • {coverage:.2f}% coverage",
    ).add_to(group)

    # Layer 2: brighter inner water body
    inner = radius * .64
    folium.Circle(
        [lat, lon],
        radius=inner,
        color="#36a8ff",
        weight=1,
        fill=True,
        fill_color="#1b9cff",
        fill_opacity=opacity * .82,
        opacity=.85,
        tooltip=f"{level} flood signal",
    ).add_to(group)

    # Layer 3: subtle translucent water ripple.
    # This is purely a visual treatment; it does not alter the
    # Flood model result or claim pixel-level georeferencing.
    ripple = radius * .78
    folium.Circle(
        [lat, lon],
        radius=ripple,
        color="#55c7ff",
        weight=1,
        fill=False,
        opacity=.32,
        dash_array="4 6",
    ).add_to(group)

    # Layer 4: small bright core to give the affected region
    # a liquid/watery highlight similar to the reference style.
    core = radius * .30
    folium.Circle(
        [lat, lon],
        radius=core,
        color="#66d2ff",
        weight=.8,
        fill=True,
        fill_color="#2bb7ff",
        fill_opacity=opacity * .38,
        opacity=.6,
    ).add_to(group)

    group.add_to(m)


def add_landslide_visual(
    m,
    lat,
    lon,
    mask,
    coverage,
    level,
    show_red=True,
):
    """
    Landslide V5 returns a 128x128 binary mask. It is displayed
    as a red detection overlay over a compact analysis footprint.

    The pipeline currently returns the mask but not its exact
    geospatial affine transform, so the overlay is intentionally
    presented as a detection footprint around the selected point,
    not as a claim of exact map registration.
    """

    group = folium.FeatureGroup(
        name="Landslide Affected Area",
        show=show_red,
    )

    # If a valid mask exists, turn it into a transparent red
    # RGBA image. Folium can display it directly.
    try:
        import numpy as np
        from PIL import Image

        arr = np.asarray(mask, dtype=np.uint8)

        if arr.ndim == 2 and arr.size > 0:
            # Normalize to 0/1.
            binary = (arr > 0).astype(np.uint8)

            # Red RGBA image; transparent background.
            rgba = np.zeros(
                (binary.shape[0], binary.shape[1], 4),
                dtype=np.uint8
            )
            rgba[:, :, 0] = 255
            rgba[:, :, 1] = 55
            rgba[:, :, 2] = 70
            rgba[:, :, 3] = binary * 175

            # Compact approximately 10 km x 10 km display window.
            # The exact geographic transform is not returned by
            # the current landslide pipeline.
            half_lat = 0.045
            half_lon = 0.055

            image = Image.fromarray(rgba, mode="RGBA")

            import base64
            from io import BytesIO

            buffer = BytesIO()
            image.save(buffer, format="PNG")
            encoded = base64.b64encode(
                buffer.getvalue()
            ).decode("utf-8")

            folium.raster_layers.ImageOverlay(
                image=(
                    "data:image/png;base64,"
                    + encoded
                ),
                bounds=[
                    [lat - half_lat, lon - half_lon],
                    [lat + half_lat, lon + half_lon],
                ],
                opacity=.72,
                interactive=True,
                cross_origin=False,
                zindex=5,
            ).add_to(group)

    except Exception:
        # The visual fallback below still provides a red
        # affected-area indication if image creation fails.
        pass

    # Red outline gives a stable visual footprint even when the
    # binary mask is extremely sparse.
    if level == "HIGH":
        outer_radius = 4800
    elif level == "MEDIUM":
        outer_radius = 3700
    else:
        outer_radius = 2900

    folium.Circle(
        [lat, lon],
        radius=outer_radius,
        color="#ff3f4f",
        weight=1.4,
        fill=False,
        opacity=.75,
        tooltip=f"Landslide detection • {coverage:.2f}% coverage",
    ).add_to(group)

    group.add_to(m)


def build_map(
    mode,
    lat,
    lon,
):
    """
    Build one map per page, keeping the visual language consistent.

    mode:
      dashboard -> blue flood + red landslide
      flood     -> blue flood
      landslide -> red landslide
    """

    zoom = 10 if mode == "dashboard" else 11

    m = folium.Map(
        location=[lat, lon],
        zoom_start=zoom,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )

    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/"
            "ArcGIS/rest/services/World_Imagery/"
            "MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri",
        name="Satellite",
        overlay=False,
        control=True,
    ).add_to(m)

    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/"
            "ArcGIS/rest/services/"
            "Reference/World_Boundaries_and_Places/"
            "MapServer/tile/{z}/{y}/{x}"
        ),
        attr="Esri",
        name="Labels",
        overlay=True,
        control=True,
        opacity=1,
    ).add_to(m)

    if mode in ("dashboard", "flood"):

        add_flood_visual(
            m,
            lat,
            lon,
            flood_coverage,
            flood_level,
            show_blue=True,
        )

    if mode in ("dashboard", "landslide") and slide_ok:

        add_landslide_visual(
            m,
            lat,
            lon,
            landslide.get("mask", []),
            slide_coverage,
            slide_level,
            show_red=True,
        )

    folium.Marker(
        [lat, lon],
        tooltip=st.session_state.location_name,
        popup=(
            f"<b>DisasterLens AI</b><br>"
            f"{html.escape(st.session_state.location_name)}<br>"
            f"Coordinates: {lat:.4f}, {lon:.4f}"
        ),
        icon=folium.Icon(
            color="blue",
            icon="info-sign",
        ),
    ).add_to(m)

    # Dashboard legend
    if mode == "dashboard":
        legend = """
        <div style="
            position:fixed;
            bottom:18px;
            right:18px;
            z-index:9999;
            background:rgba(6,16,27,.95);
            border:1px solid rgba(255,255,255,.14);
            border-radius:9px;
            padding:9px 11px;
            width:155px;
            color:white;
            font:11px Arial,sans-serif;
            box-shadow:0 8px 22px rgba(0,0,0,.35);
        ">
            <div style="font-weight:800;margin-bottom:7px;">
                Hazard Layers
            </div>
            <div style="margin:5px 0;">
                <span style="
                    display:inline-block;width:11px;height:11px;
                    background:#1688ff;border-radius:3px;
                    margin-right:7px;
                "></span>
                Flood affected area
            </div>
            <div style="margin:5px 0;">
                <span style="
                    display:inline-block;width:11px;height:11px;
                    background:#ff3f4f;border-radius:3px;
                    margin-right:7px;
                "></span>
                Landslide detection
            </div>
        </div>
        """

    elif mode == "flood":
        legend = """
        <div style="
            position:fixed;
            bottom:18px;
            right:18px;
            z-index:9999;
            background:rgba(6,16,27,.95);
            border:1px solid rgba(255,255,255,.14);
            border-radius:9px;
            padding:9px 11px;
            width:155px;
            color:white;
            font:11px Arial,sans-serif;
        ">
            <div style="font-weight:800;margin-bottom:7px;">
                Flood Segmentation
            </div>
            <div>
                <span style="
                    display:inline-block;width:11px;height:11px;
                    background:#1688ff;border-radius:3px;
                    margin-right:7px;
                "></span>
                Affected area
            </div>
        </div>
        """

    else:
        legend = """
        <div style="
            position:fixed;
            bottom:18px;
            right:18px;
            z-index:9999;
            background:rgba(6,16,27,.95);
            border:1px solid rgba(255,255,255,.14);
            border-radius:9px;
            padding:9px 11px;
            width:155px;
            color:white;
            font:11px Arial,sans-serif;
        ">
            <div style="font-weight:800;margin-bottom:7px;">
                Landslide Segmentation
            </div>
            <div>
                <span style="
                    display:inline-block;width:11px;height:11px;
                    background:#ff3f4f;border-radius:3px;
                    margin-right:7px;
                "></span>
                Detected area
            </div>
        </div>
        """

    m.get_root().html.add_child(
        folium.Element(legend)
    )

    folium.LayerControl(
        position="topright",
        collapsed=True,
    ).add_to(m)

    # Keep the dashboard map focused on the selected analysis area.
    # Presentation-only: no model, API, or prediction behavior changes.
    if mode == "dashboard":
        m.fit_bounds(
            [[lat - 0.52, lon - 0.62], [lat + 0.52, lon + 0.62]],
            padding=(12, 12),
            max_zoom=10,
        )

    return m


# ============================================================
# DASHBOARD — COMMAND CENTER
# ============================================================

# Current map coordinates from the existing working session state.
# Keep this frontend-only accessor in the page scope so build_map()
# receives the same coordinates used by the original application.
lat = st.session_state.latitude
lon = st.session_state.longitude

if page == "Dashboard":

    map_col, overview_col = st.columns(
        [3.55, 1.45],
        gap="small"
    )

    with map_col:

        st.html(
            """
            <div class="map-card">
                <div class="map-head">
                    <div>
                        <div class="map-title">🛰️ Live Multi-Hazard Satellite Map</div>
                        <div class="map-sub">
                            Sentinel-1 + Sentinel-2 • Flood and landslide detection layers
                        </div>
                    </div>
                    <div class="layer-chip">● LIVE MONITORING</div>
                </div>
            </div>
            """
        )

        m = build_map("dashboard", lat, lon)

        components.html(
            m.get_root().render(),
            height=465,
            scrolling=False,
        )

    with overview_col:

        # Flood overview
        flood_status = clean_level(flood_level)
        flood_status_color = risk_color(flood_status)

        mean_probability = safe_float(
            landslide.get("mean_probability", 0)
            if isinstance(landslide, dict) else 0
        )
        max_probability = safe_float(
            landslide.get("max_probability", 0)
            if isinstance(landslide, dict) else 0
        )

        st.html(
            f"""
            <div class="dashboard-overview">

                <div class="hazard-heading">HAZARD OVERVIEW</div>

                <div class="overview-card">
                    <div class="ov-title">
                        <span>🌊 Flood Risk Overview</span>
                        <span class="ov-status">{html.escape(flood_status)}</span>
                    </div>
                    <div class="ov-value" style="color:{flood_status_color};">
                        {flood_coverage:.2f}%
                    </div>
                    <div class="ov-label">Sentinel-1 SAR • U-Net V3 • affected coverage</div>

                    <div class="overview-grid">
                        <div class="overview-kpi">
                            <span>Confidence</span>
                            <b>{safe_float(fc.get("model_confidence")):.1f}%</b>
                        </div>
                        <div class="overview-kpi">
                            <span>24H Rain</span>
                            <b>{safe_float(fw.get("next_24h_rainfall_mm")):.1f} mm</b>
                        </div>
                    </div>
                </div>

                <div class="overview-card slide">
                    <div class="ov-title">
                        <span>⛰️ Landslide Risk Overview</span>
                        <span class="ov-status">{html.escape(clean_level(slide_level))}</span>
                    </div>
                    <div class="ov-value" style="color:{risk_color(slide_level)};">
                        {slide_coverage:.2f}%
                    </div>
                    <div class="ov-label">Sentinel-2 + DEM • U-Net V5 • detected coverage</div>

                    <div class="overview-grid">
                        <div class="overview-kpi">
                            <span>Mean Probability</span>
                            <b>{mean_probability:.3f}</b>
                        </div>
                        <div class="overview-kpi">
                            <span>Max Probability</span>
                            <b>{max_probability:.3f}</b>
                        </div>
                    </div>
                </div>

                <div class="selected-card">
                    <div class="selected-title">📍 Selected Area</div>
                    <div class="selected-location">{html.escape(str(st.session_state.location_name))}</div>
                    <div class="overview-grid">
                        <div class="overview-kpi">
                            <span>Latitude</span>
                            <b>{lat:.4f}</b>
                        </div>
                        <div class="overview-kpi">
                            <span>Longitude</span>
                            <b>{lon:.4f}</b>
                        </div>
                    </div>
                </div>
            </div>
            """
        )

        if st.session_state.running:
            st.html(
                '<div class="loading-box">Running live satellite analysis...</div>'
            )


# ============================================================
# DASHBOARD COMMAND-CENTER CARDS
# ============================================================

if page == "Dashboard":

    def _forecast_bar(period, label):
        risk = ff.get(period, {}) if isinstance(ff, dict) else {}
        score = max(0.0, min(1.0, safe_float(risk.get("score"))))
        level = clean_level(risk.get("level", "UNKNOWN"))
        return f"""
            <div class="forecast-row">
                <div class="forecast-label">{label}</div>
                <div class="forecast-track">
                    <div class="forecast-fill" style="width:{score*100:.0f}%;"></div>
                </div>
                <div class="forecast-level" style="color:{risk_color(level)};">
                    {score:.2f}
                </div>
            </div>
        """

    # Build three information-rich cards from values already returned
    # by the existing analysis pipeline.
    flood_forecast_html = "".join([
        _forecast_bar("24h", "24 H"),
        _forecast_bar("48h", "48 H"),
        _forecast_bar("72h", "72 H"),
    ])

    weather_rain = safe_float(fw.get("next_24h_rainfall_mm"))
    weather_humidity = safe_float(fw.get("average_humidity_24h_percent"))
    weather_wind = safe_float(fw.get("average_wind_speed_24h_kmh"))

    alert_rows = []
    if flood_level not in ("UNKNOWN", ""):
        alert_rows.append(
            f'<div class="alert-row"><span class="alert-dot {"high" if flood_level == "HIGH" else "warn" if flood_level == "MEDIUM" else ""}"></span>'
            f'<div style="flex:1"><div class="alert-name">Flood signal · {html.escape(flood_level)}</div>'
            f'<div class="alert-sub">{flood_coverage:.2f}% affected coverage</div></div></div>'
        )
    if slide_level not in ("UNKNOWN", ""):
        alert_rows.append(
            f'<div class="alert-row"><span class="alert-dot {"high" if slide_level == "HIGH" else "warn" if slide_level == "MEDIUM" else ""}"></span>'
            f'<div style="flex:1"><div class="alert-name">Landslide signal · {html.escape(slide_level)}</div>'
            f'<div class="alert-sub">{slide_coverage:.2f}% detected coverage</div></div></div>'
        )
    alert_rows.append(
        f'<div class="alert-row"><span class="alert-dot {"warn" if weather_rain > 10 else ""}"></span>'
        f'<div style="flex:1"><div class="alert-name">Weather context</div>'
        f'<div class="alert-sub">{weather_rain:.1f} mm rain • {weather_wind:.1f} km/h wind • {weather_humidity:.0f}% humidity</div></div></div>'
    )

    st.html(
        f"""
        <div class="command-grid">

            <div class="command-card flood-card">
                <div class="command-head">
                    <div class="command-title">📈 Flood Prediction <span style="color:#6d8498;font-weight:600;">(Next 72 Hours)</span></div>
                    <div class="command-meta">U-Net V3</div>
                </div>
                {flood_forecast_html}
                <div style="display:flex;justify-content:space-between;margin-top:9px;color:#536f86;font-size:.47rem;">
                    <span>Lower signal</span><span>Higher signal</span>
                </div>
            </div>

            <div class="command-card slide-card">
                <div class="command-head">
                    <div class="command-title">🎯 Hazard Signals</div>
                    <div class="command-meta">LIVE</div>
                </div>

                <div class="signal-row">
                    <div>
                        <div class="signal-name">Flood coverage</div>
                        <div class="signal-sub">Sentinel-1 SAR</div>
                    </div>
                    <div class="signal-value" style="color:{risk_color(flood_level)};">{flood_coverage:.2f}%</div>
                </div>

                <div class="signal-row">
                    <div>
                        <div class="signal-name">Landslide probability</div>
                        <div class="signal-sub">Maximum model signal</div>
                    </div>
                    <div class="signal-value" style="color:{risk_color(slide_level)};">{max_probability:.3f}</div>
                </div>

                <div class="signal-row">
                    <div>
                        <div class="signal-name">Satellite status</div>
                        <div class="signal-sub">Latest available imagery</div>
                    </div>
                    <div class="signal-value" style="color:#35df88;">READY</div>
                </div>
            </div>

            <div class="command-card alert-card">
                <div class="command-head">
                    <div class="command-title">🔔 Current Indicators</div>
                    <div class="command-meta">LOCAL</div>
                </div>
                {''.join(alert_rows)}
            </div>

        </div>

        <div class="system-strip">
            <div class="system-chip">
                <div class="chip-label">Flood Model</div>
                <div class="chip-value">U-Net V3</div>
            </div>
            <div class="system-chip">
                <div class="chip-label">Landslide Model</div>
                <div class="chip-value">U-Net V5</div>
            </div>
            <div class="system-chip">
                <div class="chip-label">Satellite Sources</div>
                <div class="chip-value">Sentinel-1 SAR • Sentinel-2</div>
            </div>
            <div class="system-chip">
                <div class="chip-label">Geospatial</div>
                <div class="chip-value">Google Earth Engine</div>
            </div>
        </div>
        """
    )



# ============================================================
# FLOOD-ONLY PAGE
# ============================================================

elif page == "Flood":

    left, right = st.columns(
        [3.95, 1.35],
        gap="small"
    )

    with left:

        st.html(
            """
            <div class="map-card">
                <div class="map-head">
                    <div>
                        <div class="map-title">
                            🌊 Live Flood Segmentation
                        </div>
                        <div class="map-sub">
                            Sentinel-1 SAR • Flood V3 U-Net • Blue affected-area visualization
                        </div>
                    </div>
                    <div class="layer-chip">● LIVE</div>
                </div>
            </div>
            """
        )

        m = build_map(
            "flood",
            lat,
            lon,
        )

        components.html(
            m.get_root().render(),
            height=450,
            scrolling=False,
        )

    with right:

        st.html(
            f"""
            <div class="page-card">

                <div class="analysis-title">
                    🌊 Flood Risk Overview
                </div>

                <div class="gauge">
                    <div class="gauge-arc"></div>
                    <div class="gauge-label">
                        <div class="gauge-risk"
                             style="color:{risk_color(flood_level)};">
                            {flood_level}
                        </div>
                        <div class="gauge-score">
                            Current flood signal
                        </div>
                    </div>
                </div>

                <div class="metric-grid">
                    <div class="metric">
                        <div class="metric-label">Flooded Coverage</div>
                        <div class="metric-value">
                            {flood_coverage:.2f}%
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Confidence</div>
                        <div class="metric-value">
                            {safe_float(fc.get("model_confidence")):.2f}%
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">24H Rainfall</div>
                        <div class="metric-value">
                            {safe_float(fw.get("next_24h_rainfall_mm")):.1f} mm
                        </div>
                    </div>
                    <div class="metric">
                        <div class="metric-label">Temperature</div>
                        <div class="metric-value">
                            {safe_float(fw.get("average_temperature_24h_c")):.1f} °C
                        </div>
                    </div>
                </div>

                <div class="mini-section">SATELLITE</div>

                <div class="metric">
                    <div class="metric-label">Latest Sentinel-1 Image</div>
                    <div class="metric-value">
                        {safe_text(short_date(fc.get("satellite_image_date")))}
                    </div>
                </div>

                <div class="mini-section">FUTURE RISK</div>
            </div>
            """
        )

        for period, label in [
            ("24h", "24 HOURS"),
            ("48h", "48 HOURS"),
            ("72h", "72 HOURS"),
        ]:

            risk = ff.get(period, {}) if isinstance(ff, dict) else {}
            score = safe_float(risk.get("score"))
            level = clean_level(risk.get("level", "UNKNOWN"))

            st.html(
                f"""
                <div class="future-row">
                    <div class="future-time">{label}</div>
                    <div class="future-score">Risk Score · {score:.2f}</div>
                    <div class="future-level"
                         style="color:{risk_color(level)};">
                        {level}
                    </div>
                </div>
                """
            )

    st.html(
        f"""
        <div class="compact-strip">

            <div class="strip-card">
                <div class="strip-title">MODEL</div>
                <div class="strip-value">
                    U-Net V3 • Threshold 0.35
                </div>
            </div>

            <div class="strip-card">
                <div class="strip-title">WEATHER</div>
                <div class="strip-value">
                    {safe_float(fw.get("average_humidity_24h_percent")):.0f}% humidity
                    • {safe_float(fw.get("average_wind_speed_24h_kmh")):.1f} km/h wind
                </div>
            </div>

            <div class="strip-card">
                <div class="strip-title">LOCATION</div>
                <div class="strip-value">
                    {safe_text(st.session_state.location_name)}
                </div>
            </div>

        </div>
        """
    )

    st.html(
        """
        <div class="page-note">
            Blue is reserved for the Flood layer on this page. The current
            Flood pipeline provides predicted coverage and risk but does not
            return a georeferenced pixel mask to the frontend, so the blue
            footprint is a risk-area visualization rather than a fabricated
            pixel-level segmentation.
        </div>
        """
    )


# ============================================================
# LANDSLIDE-ONLY PAGE
# ============================================================

elif page == "Landslide":

    left, right = st.columns(
        [3.95, 1.35],
        gap="small"
    )

    with left:

        st.html(
            """
            <div class="map-card">
                <div class="map-head">
                    <div>
                        <div class="map-title">
                            ⛰️ Live Landslide Segmentation
                        </div>
                        <div class="map-sub">
                            Sentinel-2 + ALOS DEM • Landslide V5 U-Net • Red detection overlay
                        </div>
                    </div>
                    <div class="layer-chip">● LIVE</div>
                </div>
            </div>
            """
        )

        m = build_map(
            "landslide",
            lat,
            lon,
        )

        components.html(
            m.get_root().render(),
            height=450,
            scrolling=False,
        )

    with right:

        mean_probability = safe_float(
            landslide.get("mean_probability", 0)
            if isinstance(landslide, dict)
            else 0
        )

        max_probability = safe_float(
            landslide.get("max_probability", 0)
            if isinstance(landslide, dict)
            else 0
        )

        positive_pixels = int(
            safe_float(
                landslide.get("landslide_pixels", 0)
                if isinstance(landslide, dict)
                else 0
            )
        )

        total_pixels = int(
            safe_float(
                landslide.get("total_pixels", 16384)
                if isinstance(landslide, dict)
                else 16384
            )
        )

        acquisition = (
            landslide.get("acquisition_date")
            if isinstance(landslide, dict)
            else None
        )

        st.html(
            f"""
            <div class="page-card">

                <div class="analysis-title">
                    ⛰️ Landslide Risk Overview
                </div>

                <div class="gauge">
                    <div class="gauge-arc"
                         style="
                            background:conic-gradient(
                                from 270deg,
                                #35df88 0deg,
                                #b7dc45 48deg,
                                #f5c84c 82deg,
                                #ff9f32 120deg,
                                #ff3f4f 180deg,
                                transparent 180deg,
                                transparent 360deg
                            );
                         ">
                    </div>

                    <div class="gauge-label">
                        <div class="gauge-risk"
                             style="color:{risk_color(slide_level)};">
                            {slide_level}
                        </div>
                        <div class="gauge-score">
                            Landslide detection signal
                        </div>
                    </div>
                </div>

                <div class="metric-grid">

                    <div class="metric">
                        <div class="metric-label">Affected Area</div>
                        <div class="metric-value">
                            {slide_coverage:.2f}%
                        </div>
                    </div>

                    <div class="metric">
                        <div class="metric-label">Mean Probability</div>
                        <div class="metric-value">
                            {mean_probability:.3f}
                        </div>
                    </div>

                    <div class="metric">
                        <div class="metric-label">Max Probability</div>
                        <div class="metric-value">
                            {max_probability:.3f}
                        </div>
                    </div>

                    <div class="metric">
                        <div class="metric-label">Detected Pixels</div>
                        <div class="metric-value">
                            {positive_pixels:,} / {total_pixels:,}
                        </div>
                    </div>

                </div>

                <div class="mini-section">SATELLITE</div>

                <div class="metric">
                    <div class="metric-label">
                        Latest Sentinel-2 Acquisition
                    </div>
                    <div class="metric-value">
                        {safe_text(short_date(acquisition))}
                    </div>
                </div>

            </div>
            """
        )

    st.html(
        f"""
        <div class="compact-strip">

            <div class="strip-card">
                <div class="strip-title">MODEL</div>
                <div class="strip-value">
                    U-Net V5 • 9 selected channels • threshold 0.88
                </div>
            </div>

            <div class="strip-card">
                <div class="strip-title">INPUT STACK</div>
                <div class="strip-value">
                    Sentinel-2 bands + Slope + DEM
                </div>
            </div>

            <div class="strip-card">
                <div class="strip-title">LOCATION</div>
                <div class="strip-value">
                    {safe_text(st.session_state.location_name)}
                </div>
            </div>

        </div>
        """
    )

    st.html(
        """
        <div class="page-note">
            Red is reserved for the Landslide layer on this page. The V5
            pipeline returns a 128×128 predicted mask; because its current API
            response does not include a geospatial transform, the frontend
            displays that mask as a compact detection footprint around the
            selected analysis location.
        </div>
        """
    )


# ============================================================
# ANALYTICS PAGE
# ============================================================

elif page == "Analytics":

    st.html("""
        <div class="intel-hero">
            <div>
                <div class="intel-kicker">ANALYSIS CONSOLE</div>
                <div class="intel-title">📊 Disaster Intelligence Analytics</div>
                <div class="intel-sub">Interactive snapshot of the latest flood and landslide model outputs for the selected location.</div>
            </div>
            <div class="intel-live">● LIVE ANALYSIS</div>
        </div>
    """)

    metric_choice = st.selectbox(
        "Analytics view",
        ["Hazard comparison", "Flood forecast risk", "Landslide model signal"],
        key="analytics_view",
    )

    flood_cls = clean_level(flood_level).lower()
    slide_cls = clean_level(slide_level).lower()

    st.html(f"""
        <div class="analytics-kpis">
            <div class="analytics-kpi">
                <div class="k-label">Flood Coverage</div>
                <div class="k-value">{flood_coverage:.2f}%</div>
                <div class="k-sub">Sentinel-1 SAR affected coverage</div>
            </div>
            <div class="analytics-kpi">
                <div class="k-label">Flood Risk</div>
                <div class="k-value {flood_cls}">{html.escape(flood_level)}</div>
                <div class="k-sub">Current model classification</div>
            </div>
            <div class="analytics-kpi slide">
                <div class="k-label">Landslide Coverage</div>
                <div class="k-value">{slide_coverage:.2f}%</div>
                <div class="k-sub">Sentinel-2 detection footprint</div>
            </div>
            <div class="analytics-kpi slide">
                <div class="k-label">Landslide Risk</div>
                <div class="k-value {slide_cls}">{html.escape(slide_level)}</div>
                <div class="k-sub">Current model classification</div>
            </div>
        </div>
    """)

    if metric_choice == "Hazard comparison":
        flood_pct = max(0.0, min(float(flood_coverage), 100.0))
        slide_pct = max(0.0, min(float(slide_coverage), 100.0))
        st.html(f"""
            <div class="analytics-panel">
                <div class="analytics-panel-head">
                    <div class="analytics-panel-title">⚖️ Hazard Coverage Comparison</div>
                    <div class="analytics-panel-meta">CURRENT SNAPSHOT</div>
                </div>
                <div class="bar-row">
                    <div class="bar-label">🌊 Flood affected area</div>
                    <div class="bar-track"><div class="bar-fill" style="width:{flood_pct:.2f}%;"></div></div>
                    <div class="bar-value">{flood_coverage:.2f}%</div>
                </div>
                <div class="bar-row">
                    <div class="bar-label">⛰️ Landslide footprint</div>
                    <div class="bar-track"><div class="bar-fill slide" style="width:{slide_pct:.2f}%;"></div></div>
                    <div class="bar-value">{slide_coverage:.2f}%</div>
                </div>
                <div class="source-strip">
                    <div class="source-chip"><b>Flood Model</b><span>U-Net V3</span></div>
                    <div class="source-chip"><b>Landslide Model</b><span>U-Net V5</span></div>
                    <div class="source-chip"><b>Flood Input</b><span>Sentinel-1 SAR</span></div>
                    <div class="source-chip"><b>Landslide Input</b><span>Sentinel-2 + DEM</span></div>
                </div>
            </div>
        """)

    elif metric_choice == "Flood forecast risk":
        forecast_rows = []
        for period, label in [("24h", "24 hours"), ("48h", "48 hours"), ("72h", "72 hours")]:
            item = ff.get(period, {}) if isinstance(ff, dict) else {}
            forecast_rows.append({
                "label": label,
                "score": safe_float(item.get("score")),
                "level": clean_level(item.get("level", "UNKNOWN")),
            })
        cards = ""
        for row in forecast_rows:
            score = max(0.0, min(row["score"], 1.0))
            lvl = row["level"].lower()
            cards += f"""
                <div class="forecast-card">
                    <div class="fc-time">{html.escape(row["label"])} horizon</div>
                    <div class="fc-score">{row["score"]:.2f}</div>
                    <div class="fc-level {lvl}" style="color:{risk_color(row["level"])};">● {html.escape(row["level"])}</div>
                    <div class="bar-track" style="margin-top:8px;"><div class="bar-fill" style="width:{score*100:.1f}%;"></div></div>
                </div>
            """
        st.html(f"""
            <div class="analytics-panel">
                <div class="analytics-panel-head">
                    <div class="analytics-panel-title">🌊 Flood Forecast Risk</div>
                    <div class="analytics-panel-meta">NEXT 72 HOURS • U-NET V3</div>
                </div>
                <div class="forecast-grid">{cards}</div>
                <div class="page-note" style="margin-top:9px;">Forecast values are the latest available application output for the selected location.</div>
            </div>
        """)

    else:
        slide_values = [
            ("Mean probability", mean_probability, "Model average signal"),
            ("Maximum probability", max_probability, "Strongest pixel signal"),
            ("Coverage", slide_coverage, "Detected area percentage"),
        ]
        cards = ""
        for label, value, sub in slide_values:
            scale = max(0.0, min(float(value if label != "Coverage" else value / 100), 1.0))
            display = f"{value:.3f}" if label != "Coverage" else f"{value:.2f}%"
            cards += f"""
                <div class="signal-card">
                    <div class="s-label">{html.escape(label)}</div>
                    <div class="s-value">{display}</div>
                    <div class="s-sub">{html.escape(sub)}</div>
                    <div class="bar-track" style="margin-top:8px;"><div class="bar-fill slide" style="width:{scale*100:.1f}%;"></div></div>
                </div>
            """
        st.html(f"""
            <div class="analytics-panel">
                <div class="analytics-panel-head">
                    <div class="analytics-panel-title">⛰️ Landslide Model Signal</div>
                    <div class="analytics-panel-meta">SENTINEL-2 + DEM • U-NET V5</div>
                </div>
                <div class="signal-grid">{cards}</div>
            </div>
        """)

    st.html("""
        <div class="source-strip">
            <div class="source-chip"><b>Geospatial</b><span>Google Earth Engine</span></div>
            <div class="source-chip"><b>Flood Model</b><span>U-Net V3</span></div>
            <div class="source-chip"><b>Landslide Model</b><span>U-Net V5</span></div>
            <div class="source-chip"><b>Analysis Scope</b><span>Latest snapshot only</span></div>
        </div>
    """)


# WEATHER PAGE
# ============================================================

elif page == "Weather":

    st.html("""
        <div class="intel-hero">
            <div>
                <div class="intel-kicker">METEOROLOGICAL CONSOLE</div>
                <div class="intel-title">🌦️ Live Weather Intelligence</div>
                <div class="intel-sub">Current conditions and forecast context for the coordinates selected in DisasterLens AI.</div>
            </div>
            <div class="intel-live">● LIVE WEATHER</div>
        </div>
    """)

    wcol1, wcol2 = st.columns([4.2, 1], gap="small")
    with wcol2:
        if st.button("↻ Refresh Weather", use_container_width=True, key="refresh_weather"):
            fetch_weather_data.clear()
            st.session_state.weather_data = None
            st.rerun()

    if st.session_state.weather_data is None:
        with st.spinner("Fetching live weather..."):
            try:
                st.session_state.weather_data = fetch_weather_data(lat, lon)
            except Exception as exc:
                st.error(f"Weather service unavailable: {exc}")

    weather = st.session_state.weather_data
    if weather:
        cur = current_weather_values(weather)
        condition = weather_text(cur["code"])

        st.html(f"""
            <div class="weather-current">
                <div class="weather-card">
                    <div class="w-label">Temperature <span class="w-icon">🌡️</span></div>
                    <div class="w-value">{cur['temperature']:.1f}°C</div>
                    <div class="w-sub">Current air temperature</div>
                </div>
                <div class="weather-card">
                    <div class="w-label">Humidity <span class="w-icon">💧</span></div>
                    <div class="w-value">{cur['humidity']:.0f}%</div>
                    <div class="w-sub">Relative humidity</div>
                </div>
                <div class="weather-card">
                    <div class="w-label">Rain <span class="w-icon">🌧️</span></div>
                    <div class="w-value">{cur['rain']:.1f} mm</div>
                    <div class="w-sub">Current precipitation</div>
                </div>
                <div class="weather-card">
                    <div class="w-label">Wind <span class="w-icon">💨</span></div>
                    <div class="w-value">{cur['wind']:.1f}</div>
                    <div class="w-sub">km/h • 10 m height</div>
                </div>
                <div class="weather-card">
                    <div class="w-label">Condition <span class="w-icon">☁️</span></div>
                    <div class="w-value" style="font-size:.96rem;">{html.escape(condition)}</div>
                    <div class="w-sub">Weather code {html.escape(str(cur['code']))}</div>
                </div>
            </div>
        """)

        weather_df = weather_dataframe(weather)
        chart_metric = st.selectbox(
            "Forecast metric",
            ["Max °C", "Min °C", "Rain mm", "Rain probability %", "Max wind km/h"],
            key="weather_chart_metric",
        )

        # Build a compact SVG trend from the same forecast dataframe.
        values = [safe_float(v) for v in weather_df[chart_metric].tolist()]
        dates = weather_df["Date"].tolist()
        if values:
            vmin, vmax = min(values), max(values)
            span = vmax - vmin if vmax != vmin else 1.0
            W, H, pad = 900, 190, 18
            pts = []
            for idx, val in enumerate(values):
                x = pad + (idx / max(1, len(values)-1)) * (W - 2*pad)
                y = H - pad - ((val - vmin) / span) * (H - 2*pad)
                pts.append((x,y))
            points = " ".join(f"{x:.1f},{y:.1f}" for x,y in pts)
            area_points = f"{pad},{H-pad} " + points + f" {W-pad},{H-pad}"
            circles = "".join(
                f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="#42b4ff" stroke="#07131f" stroke-width="2"/>'
                for x,y in pts
            )
            labels = ""
            for idx,(x,y) in enumerate(pts):
                if idx < len(dates):
                    labels += f'<text x="{x:.1f}" y="{H-2:.1f}" text-anchor="middle" fill="#607b92" font-size="10">{pd.Timestamp(dates[idx]).strftime("%a %d")}</text>'
            svg = f"""
                <svg class="weather-svg" viewBox="0 0 {W} {H}" preserveAspectRatio="none">
                    <defs>
                        <linearGradient id="weatherFill" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stop-color="#1688ff" stop-opacity=".24"/>
                            <stop offset="100%" stop-color="#1688ff" stop-opacity="0"/>
                        </linearGradient>
                    </defs>
                    <line x1="{pad}" y1="45" x2="{W-pad}" y2="45" stroke="#17334a" stroke-width="1"/>
                    <line x1="{pad}" y1="90" x2="{W-pad}" y2="90" stroke="#17334a" stroke-width="1"/>
                    <line x1="{pad}" y1="135" x2="{W-pad}" y2="135" stroke="#17334a" stroke-width="1"/>
                    <polygon points="{area_points}" fill="url(#weatherFill)"/>
                    <polyline points="{points}" fill="none" stroke="#48b3ff" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>
                    {circles}
                    {labels}
                </svg>
            """
        else:
            svg = '<div class="page-note">No forecast points are currently available.</div>'

        st.html(f"""
            <div class="weather-chart-panel">
                <div class="weather-chart-head">
                    <div class="weather-chart-title">📈 {html.escape(chart_metric)} Forecast</div>
                    <div class="weather-chart-meta">NEXT {len(weather_df)} AVAILABLE DAYS</div>
                </div>
                {svg}
            </div>
        """)

        # Seven compact forecast cards from the same dataframe.
        day_cards = ""
        for _, row in weather_df.head(7).iterrows():
            day_cards += f"""
                <div class="weather-day">
                    <div class="day">{row['Date'].strftime('%a %d')}</div>
                    <div class="cond">{html.escape(str(row['Condition']))}</div>
                    <div class="temp">{safe_float(row['Max °C']):.0f}° / {safe_float(row['Min °C']):.0f}°</div>
                    <div class="rain">💧 {safe_float(row['Rain probability %']):.0f}% • {safe_float(row['Rain mm']):.1f} mm</div>
                </div>
            """
        st.html(f'<div class="weather-days">{day_cards}</div>')

        st.html("""
            <div class="weather-note">
                Weather data is forecast information and should not be interpreted as an official emergency warning.
            </div>
        """)


# ALERTS PAGE
# ============================================================

elif page == "Alerts":

    st.html("""
        <div class="intel-hero">
            <div>
                <div class="intel-kicker">EARLY WARNING CONSOLE</div>
                <div class="intel-title">🔔 Hazard & Weather Alert Center</div>
                <div class="intel-sub">Transparent application indicators generated from the latest model outputs and local weather forecast.</div>
            </div>
            <div class="intel-live">● LIVE INDICATORS</div>
        </div>
    """)

    # Make sure weather-based indicators have data.
    if st.session_state.weather_data is None:
        try:
            st.session_state.weather_data = fetch_weather_data(lat, lon)
        except Exception:
            pass

    alerts = build_alerts()
    severity_options = ["HIGH", "MEDIUM", "LOW"]
    hazard_options = sorted(set(a[1] for a in alerts)) if alerts else ["Flood", "Landslide", "Weather"]

    f1, f2, f3 = st.columns([1, 1, 1.2])
    with f1:
        severity_filter = st.multiselect("Severity", severity_options, default=severity_options, key="alert_severity")
    with f2:
        hazard_filter = st.multiselect("Hazard", hazard_options, default=hazard_options, key="alert_hazard")
    with f3:
        active_count = sum(1 for a in alerts if a[0] in severity_filter and a[1] in hazard_filter)
        st.html(f"""
            <div class="alert-summary-card" style="margin-top:1.55rem;">
                <div class="as-label">Active indicators</div>
                <div class="as-value">{active_count}</div>
            </div>
        """)

    filtered = [a for a in alerts if a[0] in severity_filter and a[1] in hazard_filter]
    high_count = sum(1 for a in filtered if a[0] == "HIGH")
    medium_count = sum(1 for a in filtered if a[0] == "MEDIUM")
    low_count = sum(1 for a in filtered if a[0] == "LOW")

    st.html(f"""
        <div class="alert-summary">
            <div class="alert-summary-card">
                <div class="as-label">Selected indicators</div>
                <div class="as-value">{len(filtered)}</div>
            </div>
            <div class="alert-summary-card high">
                <div class="as-label">High severity</div>
                <div class="as-value">{high_count}</div>
            </div>
            <div class="alert-summary-card medium">
                <div class="as-label">Medium severity</div>
                <div class="as-value">{medium_count}</div>
            </div>
            <div class="alert-summary-card low">
                <div class="as-label">Low severity</div>
                <div class="as-value">{low_count}</div>
            </div>
        </div>
    """)

    if not filtered:
        st.html("""
            <div class="alert-list">
                <div class="alert-list-head">
                    <div class="alert-list-title">🟢 No Matching Indicators</div>
                    <div class="alert-list-meta">CURRENT ANALYSIS</div>
                </div>
                <div class="page-note" style="padding:12px 0 4px;">
                    No matching application-level alert indicators were found for the current filters.
                </div>
            </div>
        """)
    else:
        rows = ""
        for severity, hazard, message in filtered:
            sev = severity.lower()
            rows += f"""
                <div class="alert-row-new">
                    <span class="alert-sev-dot {sev}"></span>
                    <div class="alert-severity {sev}">{html.escape(severity)}</div>
                    <div>
                        <div class="alert-hazard">{html.escape(hazard)}</div>
                        <div class="alert-message">{html.escape(message)}</div>
                    </div>
                    <div class="alert-time">CURRENT<br>ANALYSIS</div>
                </div>
            """
        st.html(f"""
            <div class="alert-list">
                <div class="alert-list-head">
                    <div class="alert-list-title">🚨 Current Indicators</div>
                    <div class="alert-list-meta">{len(filtered)} MATCHING SIGNALS</div>
                </div>
                {rows}
            </div>
        """)

    st.html("""
        <div class="alert-disclaimer">
            ℹ️ These are DisasterLens AI application indicators, not official government emergency alerts.
            Use them as analytical context alongside authoritative local emergency information.
        </div>
    """)


# REPORTS PAGE
# ============================================================

elif page == "Reports":

    st.html("""
        <div class="system-hero">
            <div class="system-hero-title">📄 Disaster Analysis Report</div>
            <div class="system-hero-sub">Review the current analysis and export the same snapshot as HTML, CSV, JSON or PDF.</div>
        </div>
    """)

    report_df = make_report_data()
    st.session_state.report_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    r1, r2, r3 = st.columns(3)
    with r1:
        st.download_button(
            "⬇ Download CSV",
            data=report_df.to_csv(index=False).encode("utf-8"),
            file_name="disasterlens_report.csv",
            mime="text/csv",
            use_container_width=True,
            key="download_report_csv",
        )
    with r2:
        report_json = json.dumps(report_df.to_dict(orient="records"), indent=2, ensure_ascii=False)
        st.download_button(
            "⬇ Download JSON",
            data=report_json.encode("utf-8"),
            file_name="disasterlens_report.json",
            mime="application/json",
            use_container_width=True,
            key="download_report_json",
        )
    with r3:
        report_html = make_report_html(report_df)
        st.download_button(
            "⬇ Download HTML",
            data=report_html.encode("utf-8"),
            file_name="disasterlens_report.html",
            mime="text/html",
            use_container_width=True,
            key="download_report_html",
        )

    pdf_bytes = make_report_pdf(report_df)
    if pdf_bytes:
        st.download_button(
            "⬇ Download PDF Report",
            data=pdf_bytes,
            file_name="disasterlens_report.pdf",
            mime="application/pdf",
            use_container_width=True,
            key="download_report_pdf",
        )

    st.html(
        f"""
        <div class="report-preview" style="margin-top:9px;">
            <h2>DisasterLens AI — Analysis Report</h2>
            <div style="color:#6b7d8e;font-size:11px;">{safe_text(st.session_state.location_name)} · Generated {st.session_state.report_timestamp}</div>
            <h3>Location</h3>
            <table>
                <tr><td>Coordinates</td><td>{lat:.6f}, {lon:.6f}</td></tr>
                <tr><td>Flood Risk</td><td>{flood_level}</td></tr>
                <tr><td>Flood Coverage</td><td>{flood_coverage:.2f}%</td></tr>
                <tr><td>Landslide Risk</td><td>{slide_level}</td></tr>
                <tr><td>Landslide Coverage</td><td>{slide_coverage:.2f}%</td></tr>
                <tr><td>Flood Satellite</td><td>{safe_text(short_date(fc.get("satellite_image_date")))}</td></tr>
                <tr><td>Landslide Satellite</td><td>{safe_text(short_date(landslide.get("acquisition_date") if isinstance(landslide, dict) else None))}</td></tr>
            </table>
            <h3>Report Scope</h3>
            <p>This report summarizes the latest available DisasterLens AI model outputs and weather information for the selected analysis location.</p>
        </div>
        """
    )

    st.dataframe(report_df, use_container_width=True, hide_index=True)
    st.caption("Report values are a snapshot of the application state at generation time. They are not official emergency guidance.")


# ============================================================
# FOOTER
# ============================================================

st.html(
    """
    <div class="footer">
        🌍 DisasterLens AI • Sentinel-1 + Sentinel-2 • U-Net Deep Learning
        • Google Earth Engine • Multi-Hazard Early Warning System
    </div>
    """
)
