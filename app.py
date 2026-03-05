import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import json
import os
import time
import re
from datetime import datetime

# ==========================================
# 0. 頁面與 CSS 設定 (針對 14 吋筆電螢幕優化)
# ==========================================
st.set_page_config(page_title="NCS Swallowing Monitor", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
/* 淺色背景與緊湊佈局，極致壓縮上下邊界以適應筆電螢幕 */
.block-container { padding-top: 0.5rem; padding-bottom: 0rem; padding-left: 2rem; padding-right: 2rem; max-width: 100%; }
.stApp { background-color: #F8FAFC; color: #1E293B; font-family: 'Inter', 'Helvetica Neue', sans-serif; }

/* 淺色卡片 UI */
.custom-card {
    background-color: #FFFFFF;
    padding: 0.6rem 0.8rem;
    border-radius: 8px;
    border: 1px solid #E2E8F0;
    margin-bottom: 0.5rem;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
}

/* 文字與標籤樣式 */
h4, h5, p { margin: 0; padding: 0; }
.title-text { font-size: 1rem; font-weight: 700; color: #0F172A; margin-bottom: 4px; }
.research-tag { background-color: #EF4444; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 700; font-size: 0.7rem; letter-spacing: 0.5px;}
.text-success { color: #059669; font-weight: bold; }
.text-muted { color: #64748B; font-size: 0.75rem; line-height: 1.2; }
.value-large { font-size: 1.3rem; font-weight: 800; line-height: 1; margin: 4px 0; color: #1E293B; }

/* LLM Copilot 專屬樣式 */
.llm-disclaimer { background-color: #FEF2F2; border-left: 3px solid #DC2626; padding: 4px 8px; font-size: 0.7rem; color: #991B1B; margin-bottom: 8px; border-radius: 0 4px 4px 0;}

/* 事件紀錄表格樣式 */
.event-table { width: 100%; border-collapse: collapse; font-size: 0.75rem; margin-top: 4px; }
.event-table th { padding: 4px; text-align: left; border-bottom: 2px solid #E2E8F0; color: #64748B; font-weight: 600; }
.event-table td { padding: 4px; border-bottom: 1px solid #F1F5F9; color: #334155; }
.event-table tr:last-child td { border-bottom: none; }
.event-row-warn { background-color: #FFFBEB; }

/* ✨ 魔法 CSS：完美無縫接合 Admittance 的標題與 Plotly 圖表容器 */
div[data-testid="element-container"]:has(#adm-plot-wrapper) {
    position: relative;
    z-index: 10;
}
div[data-testid="element-container"]:has(#adm-plot-wrapper) + div[data-testid="element-container"] {
    border-left: 4px solid #8B5CF6 !important;
    border-right: 1px solid #E2E8F0 !important;
    border-bottom: 1px solid #E2E8F0 !important;
    border-bottom-left-radius: 8px !important;
    border-bottom-right-radius: 8px !important;
    background-color: #ffffff !important;
    margin-top: -15px !important; 
    padding: 0 5px 4px 5px !important;
    box-shadow: 0 2px 3px rgba(0,0,0,0.05);
    position: relative;
    z-index: 1;
}

/* 中欄 flex：Phase III 區塊 margin-top:auto 貼底，與左欄底部對齊 */
[data-testid="stHorizontalBlock"]:nth-of-type(2) > div:nth-child(2) {
    display: flex !important;
    flex-direction: column !important;
}
[data-testid="stHorizontalBlock"]:nth-of-type(2) > div:nth-child(2) > div:last-child {
    margin-top: auto !important;
}

#MainMenu, footer, header {visibility: hidden;}

/* 自訂聊天區塊卷軸樣式 */
.chat-container::-webkit-scrollbar { width: 6px; }
.chat-container::-webkit-scrollbar-track { background: transparent; }
.chat-container::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }
.chat-container::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

/* Quick Ask 按鈕自適應深色/淺色模式 */
.quick-chip button {
    border: 1px solid #E2E8F0 !important;
    background: #FFFFFF !important;
    color: #334155 !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    border-radius: 8px !important;
    transition: all 0.2s ease !important;
}
.quick-chip button:hover {
    border-color: #8B5CF6 !important;
    background: #F5F3FF !important;
    color: #6D28D9 !important;
}
@media (prefers-color-scheme: dark) {
    .quick-chip button {
        border-color: #475569 !important;
        background: #1E293B !important;
        color: #E2E8F0 !important;
    }
    .quick-chip button:hover {
        border-color: #A78BFA !important;
        background: #312E81 !important;
        color: #DDD6FE !important;
    }
}

/* 聊天輸入框更明顯 */
[data-testid="stChatInput"] {
    border: 2px solid #8B5CF6 !important;
    border-radius: 10px !important;
    box-shadow: 0 0 8px rgba(109, 40, 217, 0.25) !important;
    background: #FEFEFE !important;
}
[data-testid="stChatInput"] textarea {
    font-size: 0.85rem !important;
}
@media (prefers-color-scheme: dark) {
    [data-testid="stChatInput"] {
        border-color: #A78BFA !important;
        background: #1E293B !important;
        box-shadow: 0 0 8px rgba(167, 139, 250, 0.35) !important;
    }
}

/* AI 思考動畫 */
@keyframes typing-pulse {
    0%, 100% { opacity: 0.4; }
    50% { opacity: 1; }
}
.typing-dot {
    display: inline-block;
    width: 6px; height: 6px;
    margin: 0 2px;
    background: #8B5CF6;
    border-radius: 50%;
    animation: typing-pulse 1.2s infinite ease-in-out;
}
.typing-dot:nth-child(2) { animation-delay: 0.2s; }
.typing-dot:nth-child(3) { animation-delay: 0.4s; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* 模擬 Mac 視窗控制按鈕 */
.mac-buttons {
    display: flex;
    gap: 8px;
    padding: 2px 0 0 0; /* 更靠左上角 */
    position: absolute;
    top: 0;
    left: 0;
    z-index: 9999;
}
.dot {
    width: 12px;
    height: 12px;
    border-radius: 50%;
}
.red { background-color: #FF5F56; }
.yellow { background-color: #FFBD2E; }
.green { background-color: #27C93F; }
</style>

<div class="mac-buttons">
    <div class="dot red"></div>
    <div class="dot yellow"></div>
    <div class="dot green"></div>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 1. 讀取真實資料 
# ==========================================
@st.cache_data
def load_real_data():
    if os.path.exists('demo_signals.csv') and os.path.exists('demo_events.json'):
        df = pd.read_csv('demo_signals.csv')
        with open('demo_events.json', 'r', encoding='utf-8') as f:
            events = json.load(f)
        return df['Time'].values, df['Tx1Rx1_mag'].values, df['Tx2Rx2_mag'].values, events
    else:
        t = np.linspace(0, 15, 1500)
        ch1 = np.zeros_like(t)
        ch2 = np.zeros_like(t)
        events = [{'type':'water', 'start':3.0, 'end':4.5, 'delay':0.072}, {'type':'dry', 'start':10.0, 'end':11.5, 'delay':0.418}]
        return t, ch1, ch2, events

t, ch1, ch2, events = load_real_data()

# ==========================================
# 1.5 Rule-Based AI Response Engine
# ==========================================
DEFAULT_EMR_DRAFT = (
    "Objective:\n"
    "Current swallow profile stable. Water Δt 72 ms, dry clearance Δt 418 ms (WNL). "
    "Estimated HMPP ~145 mmHg and UES opening ~0.45 s. No sensor evidence of airway "
    "invasion (PAS < 2, conf 94%). Single isolated borderline Δt event at 12:22.\n\n"
    "Assessment:\n"
    "Functional swallow with adequate pharyngeal contractility and timing. "
    "Low short-term aspiration risk.\n\n"
    "Plan:\n"
    "1. SLP bedside evaluation to confirm oral intake safety.\n"
    "2. Continue NCS-MIMO monitoring for 7 days."
)

def get_ai_response(user_msg: str) -> dict:
    """Rule-based AI response matching keywords to pre-authored clinical templates."""
    msg = user_msg.lower().strip()

    # --- Pattern rules (checked in order, first match wins) ---
    if any(k in msg for k in ["safe", "oral", "feeding", "eat", "diet", "吃"]):
        return {
            "text": (
                "Based on current NCS-MIMO sensor biomarkers:\n\n"
                "• Water Δt = 72 ms (normal range 62-128 ms) ✅\n"
                "• Est. HMPP = ~145 mmHg (> P10 threshold of 83 mmHg) ✅\n"
                "• PAS < 2 classifier negative (confidence 94%) ✅\n\n"
                "Sensor data are **consistent with functional swallowing**. "
                "However, **oral feeding safety must be confirmed by SLP bedside evaluation** — "
                "sensor findings alone do not constitute clearance for diet advancement."
            ),
            "actions": ["📋 Insert to note", "🩺 Request SLP consult"],
        }

    if any(k in msg for k in ["borderline", "12:22", "134", "prolonged", "flag", "warning", "⚠"]):
        return {
            "text": (
                "At **12:22**, the Water Δt measured **134 ms**, slightly above the "
                "128 ms upper bound (Park 2021 normative reference).\n\n"
                "Key context:\n"
                "• This is a **single isolated event** — the remaining 46 swallows are WNL.\n"
                "• No concurrent PAS elevation or airway invasion detected.\n"
                "• Possible causes: motion artifact, partial bolus, or momentary fatigue.\n\n"
                "**Recommendation:** Monitor next 2-3 swallows. If Δt > 128 ms recurs in ≥ 3 consecutive events, "
                "escalate to SLP for clinical assessment."
            ),
            "actions": ["📋 Add to note", "⚠️ Flag for SLP"],
        }

    if any(k in msg for k in ["compare", "yesterday", "trend", "history", "過去", "趨勢"]):
        return {
            "text": (
                "📊 **7-Day Longitudinal Trend (Demo-001):**\n\n"
                "| Day | Δt-Water (ms) | Est. HMPP (mmHg) |\n"
                "|-----|:---:|:---:|\n"
                "| D1 | 75 | 142 |\n"
                "| D2 | 71 | 145 |\n"
                "| D3 | 73 | 140 |\n"
                "| D4 | 70 | 148 |\n"
                "| D5 | 72 | 146 |\n"
                "| D6 | 74 | 144 |\n"
                "| D7 (Today) | **72** | **145** |\n\n"
                "All values are **stable and within normative ranges** over 7 days. "
                "No deterioration trend detected. The longitudinal profile is consistent with "
                "a **healthy baseline**."
            ),
            "actions": ["📋 Insert to note"],
        }

    if any(k in msg for k in ["risk", "aspiration", "pas", "airway", "invasion", "風險"]):
        return {
            "text": (
                "**Aspiration Risk Assessment (Demo-001):**\n\n"
                "🟢 **Overall Risk: LOW**\n\n"
                "• PAS < 2 classifier: **Negative** (confidence 94%)\n"
                "• Airway invasion: **Not detected**\n"
                "• Water Δt: 72 ms (WNL)\n"
                "• Dry clearance Δt: 418 ms (WNL)\n"
                "• Est. HMPP: ~145 mmHg (adequate pharyngeal contractility)\n\n"
                "⚠️ Note: Sensor-based risk assessment is **decision support only**. "
                "Clinical diagnosis of aspiration risk requires VFSS/FEES gold standard."
            ),
            "actions": ["📋 Insert to note", "🔍 Show evidence"],
        }

    if any(k in msg for k in ["hmpp", "pressure", "contractility", "pharyngeal", "壓力"]):
        return {
            "text": (
                "**Estimated Hyoid-to-Mandible Peak Pressure (HMPP):**\n\n"
                "• Current estimate: **~145 mmHg** (95% CI: 132–158)\n"
                "• Model confidence: 94%\n"
                "• Normative P10 threshold: 83 mmHg (Cock 2017)\n\n"
                "The estimated HMPP is **well above the P10 threshold**, indicating "
                "adequate pharyngeal contractility. This is consistent with functional "
                "bolus propulsion.\n\n"
                "⚠️ Phase II inference — requires HRIM validation for clinical confirmation."
            ),
            "actions": ["📋 Insert to note"],
        }

    if any(k in msg for k in ["ues", "opening", "sphincter", "上食道"]):
        return {
            "text": (
                "**UES (Upper Esophageal Sphincter) Opening:**\n\n"
                "• Estimated duration: **~0.45 s** (95% CI: 0.38–0.52)\n"
                "• Model confidence: 79%\n"
                "• Status: 🟢 Normal\n\n"
                "The UES opening duration is within expected range for healthy swallowing. "
                "No evidence of impaired UES relaxation or premature closure."
            ),
            "actions": ["📋 Insert to note"],
        }

    if any(k in msg for k in ["summary", "report", "overall", "摘要", "總結"]):
        return {
            "text": (
                "**Clinical Summary — Demo-001 (PEI-EN):**\n\n"
                "Subject presents with a **functional swallow profile**. "
                "All sensor-derived biomarkers are within normative ranges:\n\n"
                "• Sequential coordination Δt: WNL (Water 72 ms, Dry 418 ms)\n"
                "• Est. HMPP: ~145 mmHg (adequate)\n"
                "• UES opening: ~0.45 s (normal)\n"
                "• PAS < 2 (no airway invasion detected)\n\n"
                "One isolated borderline Δt event at 12:22 (134 ms) — not clinically significant.\n\n"
                "**Recommendation:** SLP bedside evaluation for diet clearance. "
                "Continue 7-day NCS-MIMO monitoring."
            ),
            "actions": ["📋 Insert to note", "📤 Generate EMR draft"],
        }

    if any(k in msg for k in ["delta", "delay", "coordination", "timing", "時間", "延遲"]):
        return {
            "text": (
                "**Sequential Coordination Δt Analysis:**\n\n"
                "Δt measures the timing delay between supra- and infra-hyoid muscle activation "
                "(Tx1Rx1 → Tx2Rx2 peak onset), indicating pharyngeal coordination.\n\n"
                "• **Water bolus Δt:** 72 ms (normative: 62–128 ms) ✅\n"
                "• **Dry clearance Δt:** 418 ms (expected longer for dry swallows) ✅\n\n"
                "Both values indicate **normal sequential coordination**. "
                "The proprietary Δt biomarker is the key innovation of NCS-MIMO."
            ),
            "actions": ["📋 Insert to note", "🔍 Show evidence"],
        }

    if any(k in msg for k in ["hello", "hi", "hey", "你好", "哈囉"]):
        return {
            "text": (
                "Hello! I'm the NCS-MIMO Clinical Copilot. I can help you with:\n\n"
                "• 🔍 Interpreting sensor biomarkers (Δt, HMPP, UES)\n"
                "• ⚠️ Explaining flagged events\n"
                "• 📊 Comparing longitudinal trends\n"
                "• 📝 Generating clinical summaries\n\n"
                "Try asking: *\"Is this patient safe for oral feeding?\"* "
                "or *\"Why is the Δt borderline at 12:22?\"*"
            ),
            "actions": [],
        }

    # Fallback
    return {
        "text": (
            f"I understand you're asking about: *\"{user_msg}\"*\n\n"
            "Based on the current session for Demo-001 (PEI-EN), all sensor-derived "
            "biomarkers are within normative ranges (Water Δt 72 ms, HMPP ~145 mmHg, "
            "PAS < 2).\n\n"
            "Could you rephrase or try one of these topics?\n"
            "• Oral feeding safety\n"
            "• Borderline event at 12:22\n"
            "• Trend comparison (7-day)\n"
            "• Aspiration risk assessment\n"
            "• HMPP / UES biomarker details"
        ),
        "actions": [],
    }

# Session state initialization
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "ai",
            "content": (
                "Sensor data summary ready for Demo-001.\n"
                "• Water Δt 72 ms, Dry Δt 438 ms — both WNL.\n"
                "• Est. HMPP ~145 mmHg, no airway invasion detected (PAS < 2, confidence 94%).\n\n"
                "Suggested next step: SLP evaluation."
            ),
            "actions": ["📋 Insert to note", "🔍 Show evidence"],
            "time": "09:42 AM",
        },
        {
            "role": "user",
            "content": "Why is the Δt borderline at 12:22?",
            "actions": [],
            "time": "09:43 AM",
        },
        {
            "role": "ai",
            "content": (
                "At 12:22, Water Δt = 134 ms, slightly above the 128 ms upper bound (Park 2021).\n\n"
                "Isolated single-event deviation — not consistent with sustained impairment. "
                "Recommend monitoring next 2–3 swallows."
            ),
            "actions": ["📋 Add to note", "⚠️ Flag for SLP"],
            "time": "09:43 AM",
        },
    ]

if "emr_sent" not in st.session_state:
    st.session_state.emr_sent = False
if "editing_draft" not in st.session_state:
    st.session_state.editing_draft = False
if "draft_text" not in st.session_state:
    st.session_state.draft_text = DEFAULT_EMR_DRAFT
if "draft_discarded" not in st.session_state:
    st.session_state.draft_discarded = False
if "thinking" not in st.session_state:
    st.session_state.thinking = False

# ==========================================
# 2. 頂部 Header Bar
# ==========================================
col_h1, col_h2, col_h3 = st.columns([1.5, 2, 1])
with col_h1:
    st.markdown("<h4 style='margin-bottom:0; color: #0F172A; padding-top: 4px;'>NCS-MIMO Swallowing Monitor</h4>", unsafe_allow_html=True)
with col_h2:
    st.markdown("<div style='color: #64748B; font-size: 0.8rem; padding-top: 8px;'>"
                "<b style='color:#334155;'>Subject:</b> PEI-EN (Demo-001) │ Healthy Baseline │ <b style='color:#334155;'>Last Event:</b> 12s ago"
                "</div>", unsafe_allow_html=True)
with col_h3:
    st.markdown("<div style='text-align: right; padding-top: 6px;'><span class='research-tag'>⚠️ RESEARCH USE ONLY</span></div>", unsafe_allow_html=True)

st.markdown("<hr style='margin: 0.2rem 0 0.4rem 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

# ==========================================
# 3. 主版面佈局：左 (38%) | 中 (33%) | 右 (29%) 
# ==========================================
col_left, col_mid, col_right = st.columns([3.6, 3.4, 3.0])

# ------------------------------------------
# 左欄：視覺化波形、趨勢圖與事件偵測面板
# ------------------------------------------
with col_left:
    st.markdown("<div class='title-text'>MIMO Spatio-Temporal Mapping</div>", unsafe_allow_html=True)
    
    fig_wave = go.Figure()
    offset = np.max(ch2) - np.min(ch1) + 1 if len(ch1) > 0 else 2
    fig_wave.add_trace(go.Scatter(x=t, y=ch1 + offset, name="Tx1Rx1 (Supra)", line=dict(color="#0EA5E9", width=2)))
    fig_wave.add_trace(go.Scatter(x=t, y=ch2, name="Tx2Rx2 (Infra)", line=dict(color="#F97316", width=2)))
    
    y_below = np.min(ch2) - 0.5
    y_above = np.max(ch1) + offset + 0.5
    for e in events:
        color = "#10B981" if e['type'] == 'water' else "#8B5CF6"
        label = "Water" if e['type'] == 'water' else "Dry Clearance"
        fig_wave.add_vrect(x0=e['start'], x1=e['end'], fillcolor=color, opacity=0.1, layer="below", line_width=0)
        delay_ms = int(e['delay'] * 1000)
        y_annot = y_above if e['type'] == 'dry' else y_below
        fig_wave.add_annotation(x=e['start'] + (e['end'] - e['start']) / 2, y=y_annot,
                                text=f"{label} (Δt={delay_ms}ms)", showarrow=False, font=dict(color=color, size=9))

    fig_wave.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#475569"),
        margin=dict(l=0, r=10, t=5, b=5), height=250, 
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10)),
        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", title=dict(text="Time (s)", font=dict(size=9)), tickfont=dict(size=9)),
        yaxis=dict(showgrid=False, showticklabels=False)
    )
    st.plotly_chart(fig_wave, use_container_width=True, config={'displayModeBar': False})
    
    st.markdown("<div class='title-text' style='margin-top: -0.2rem;'>Longitudinal Trend (Healthy Baseline)</div>", unsafe_allow_html=True)
    
    days = [f"D{i}" for i in range(1, 8)]
    trend_delta = [75, 71, 73, 70, 72, 74, 72]
    trend_hmpp = [142, 145, 140, 148, 146, 144, 145]
    
    fig_trend = go.Figure()
    fig_trend.add_trace(go.Scatter(x=days, y=trend_delta, name="Δt-Water", mode='lines+markers', line=dict(color="#10B981", width=2.5), yaxis="y1"))
    fig_trend.add_trace(go.Scatter(x=days, y=trend_hmpp, name="Est. HMPP", mode='lines+markers', line=dict(color="#F59E0B", width=2.5), yaxis="y2"))
    
    fig_trend.add_hline(y=128, line_dash="dash", line_color="rgba(16, 185, 129, 0.4)", yref="y1")
    fig_trend.add_hline(y=83, line_dash="dash", line_color="rgba(245, 158, 11, 0.4)", yref="y2")
    fig_trend.add_annotation(x=0, y=135, yref="y1", text="Δt upper bound: 128 ms [Park 2021]", showarrow=False, font=dict(size=8, color="#059669"), xanchor="left")
    fig_trend.add_annotation(x=0, y=74, yref="y2", text="HMPP P10 threshold: 83 mmHg [Cock 2017]", showarrow=False, font=dict(size=8, color="#D97706"), xanchor="left")
    
    fig_trend.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", font=dict(color="#475569"),
        margin=dict(l=0, r=0, t=5, b=18),
        height=180,
        legend=dict(orientation="h", yanchor="top", y=1.2, xanchor="center", x=0.5, font=dict(size=9)),
        yaxis=dict(title=dict(text="Δt (ms)", font=dict(color="#059669", size=9)), tickfont=dict(size=9), range=[50, 150], gridcolor="#E2E8F0"),
        yaxis2=dict(title=dict(text="HMPP (mmHg)", font=dict(color="#D97706", size=9)), tickfont=dict(size=9), range=[60, 180], overlaying="y", side="right", showgrid=False)
    )
    st.plotly_chart(fig_trend, use_container_width=True, config={'displayModeBar': False})

    st.markdown("""
    <div class="custom-card" style="margin-bottom: 0;">
        <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #E2E8F0; padding-bottom: 4px;">
            <div class="title-text" style="margin: 0;">⏱️ Real-Time Event Log <span style="font-size: 0.75rem; color: #64748B; font-weight: normal;">(Past 60 min)</span></div>
            <div style="font-size: 0.7rem; color: #10B981; font-weight: bold; display: flex; align-items: center;">
                <span style="height: 6px; width: 6px; background-color: #10B981; border-radius: 50%; display: inline-block; margin-right: 4px; animation: pulse 2s infinite;"></span>Live
            </div>
        </div>
        <table class="event-table">
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Bolus Type</th>
                    <th>Δt (ms)</th>
                    <th style="text-align: center;">Status</th>
                    <th>Notes</th>
                </tr>
            </thead>
            <tbody>
                <tr><td>12:41</td><td>Water 💧</td><td>68</td><td style="text-align: center;">✅</td><td>WNL</td></tr>
                <tr><td>12:38</td><td>Dry 🪹</td><td>439</td><td style="text-align: center;">✅</td><td>WNL</td></tr>
                <tr><td>12:35</td><td>Water 💧</td><td>75</td><td style="text-align: center;">✅</td><td>WNL</td></tr>
                <tr><td>12:29</td><td>Dry 🪹</td><td>438</td><td style="text-align: center;">✅</td><td>WNL</td></tr>
                <tr class="event-row-warn"><td>12:22</td><td>Water 💧</td><td><b style="color:#D97706;">134</b></td><td style="text-align: center;">⚠️</td><td style="color:#D97706;">Borderline prolonged</td></tr>
                <tr><td>12:18</td><td>Dry 🪹</td><td>469</td><td style="text-align: center;">✅</td><td>WNL</td></tr>
            </tbody>
        </table>
        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #475569; margin-top: 6px; padding-top: 6px; border-top: 1px dashed #CBD5E1;">
            <span><b>Total Swallows:</b> 47</span>
            <span><b>Bolus Classification Acc:</b> 94%</span>
            <span><b>Flagged:</b> <span style="color: #EF4444; font-weight: bold;">1</span></span>
        </div>
    </div>
    <style>@keyframes pulse { 0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); } 70% { transform: scale(1); box-shadow: 0 0 0 4px rgba(16, 185, 129, 0); } 100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } }</style>
    """, unsafe_allow_html=True)

# ------------------------------------------
# 中欄：臨床摘要、Δt、HMPP/UES雙子星、高擬真Admittance波形、PV Loop Phenotyping
# ------------------------------------------
with col_mid:
    st.markdown("""
<div class="custom-card" style="border-left: 4px solid #10B981;">
    <div class="title-text">Clinical Risk Summary</div>
    <p style="margin: 2px 0;"><b>Aspiration Risk:</b> <span class="text-success">LOW RISK 🟢</span></p>
    <p style="margin: 2px 0;"><b>Airway Invasion:</b> Not detected</p>
    <p class="text-muted" style="margin: 0 0 2px 0; font-size: 0.75rem;">(PAS &lt; 2 classifier negative, confidence 94%)</p>
    <p style="margin: 2px 0;">✅ Sensor biomarkers within normative ranges.</p>
    <p style="margin: 2px 0;">⚠️ Dietary safety requires SLP clinical evaluation.</p>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("""
<div class="custom-card" style="border-left: 4px solid #0EA5E9;">
    <div class="title-text" style="color: #0EA5E9;">🎯 Sequential Coordination (Δt)</div>
    <div style="display: flex; justify-content: space-around; text-align: center; margin-top: 4px;">
        <div><span style="font-size: 0.75rem; color:#64748B;">Water Bolus</span><br><span class="value-large text-success" style="color:#0EA5E9;">72</span><span style="font-size:0.7em; color:#64748B;">ms</span></div>
        <div><span style="font-size: 0.75rem; color:#64748B;">Dry Clearance</span><br><span class="value-large text-success" style="color:#0EA5E9;">418</span><span style="font-size:0.7em; color:#64748B;">ms</span></div>
    </div>
    <p class="text-muted" style="border-top: 1px solid #E2E8F0; padding-top: 2px; margin-top: 4px; text-align: center; font-size: 0.7rem;">
    ★ Proprietary Biomarker │ Normative: 62-128 ms</p>
</div>
""", unsafe_allow_html=True)
    
    st.markdown("""
<div style="display: flex; gap: 0.5rem; margin-bottom: 0.3rem;">
    <div class="custom-card" style="flex: 1; border-left: 4px solid #F59E0B; padding: 0.3rem 0.6rem; margin-bottom: 0;">
        <div class="title-text" style="color: #D97706; font-size: 0.85rem;">💪 Est. HMPP</div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: baseline;">
                <p class="value-large" style="color: #D97706; font-size: 1.25rem;">~145</p><p style="font-size:0.65em; color:#64748B; margin-left:2px;">mmHg</p>
            </div>
            <div style="text-align: right;">
                <p class="text-muted" style="font-size: 0.65rem;">95% CI: [132–158] | Conf: 94%</p>
                <p class="text-success" style="font-size: 0.7rem; margin-top:2px;">🟢 > P10 (83)</p>
            </div>
        </div>
    </div>
    <div class="custom-card" style="flex: 1; border-left: 4px solid #7C3AED; padding: 0.3rem 0.6rem; margin-bottom: 0;">
        <div class="title-text" style="color: #7C3AED; font-size: 0.85rem;">🚪 UES Opening</div>
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
            <div style="display: flex; align-items: baseline;">
                <p class="value-large" style="color: #7C3AED; font-size: 1.25rem;">~0.45</p><p style="font-size:0.65em; color:#64748B; margin-left:2px;">s</p>
            </div>
            <div style="text-align: right;">
                <p class="text-muted" style="font-size: 0.65rem;">95% CI: [0.38–0.52] | Conf: 79%</p>
                <p class="text-success" style="font-size: 0.7rem; margin-top:2px;">🟢 Normal</p>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("""
<div id="adm-plot-wrapper" class="custom-card" style="margin-bottom: 0; border-bottom: none; border-bottom-left-radius: 0; border-bottom-right-radius: 0; border-left: 4px solid #8B5CF6; padding-bottom: 4px;">
    <div class="title-text" style="color: #8B5CF6;">🌊 Est. Pharyngeal Admittance</div>
    <p class="text-muted" style="font-size: 0.7rem;">Phase II Inference • <span class="text-success">🟢 Single-Peak Normal</span></p>
</div>
""", unsafe_allow_html=True)

    t_adm = np.linspace(0, 1.5, 300)
    baseline = 3.2
    peak_val = 20.5
    t_peak = 0.19 
    rise = baseline + (peak_val - baseline) * (t_adm / t_peak) ** 1.4
    rise = np.where(t_adm <= t_peak, rise, peak_val)
    decay = np.exp(-(t_adm - t_peak) / 0.32)
    shoulder = 0.28 * np.exp(-((t_adm - 0.40) / 0.09) ** 2)
    mask_fall = t_adm > t_peak
    fall_curve = np.where(mask_fall, decay + shoulder, 0.0)
    fall_max = fall_curve.max()
    if fall_max > 1e-6:
        fall_curve = np.where(mask_fall, fall_curve / fall_max, 0.0)
    fall = np.where(mask_fall, baseline + (peak_val - baseline) * fall_curve, rise)
    adm_signal = np.where(t_adm <= t_peak, rise, fall)
    adm_signal = np.clip(adm_signal, baseline - 0.5, peak_val + 0.5)
    adm_signal += np.random.normal(0, 0.25, len(t_adm)) 
    
    fig_adm = go.Figure()
    y_min_axis = -2  
    fig_adm.add_trace(go.Scatter(x=t_adm, y=np.full_like(t_adm, y_min_axis), line=dict(width=0), showlegend=False, hoverinfo='skip'))
    fig_adm.add_trace(go.Scatter(x=t_adm, y=adm_signal, fill='tonexty', fillcolor="rgba(139, 92, 246, 0.2)", line=dict(color="#8B5CF6", width=2.5)))
    
    fig_adm.update_layout(
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)", 
        margin=dict(l=0, r=0, t=2, b=2), height=80,
        xaxis=dict(showgrid=True, gridcolor="#E2E8F0", showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor="#E2E8F0", range=[y_min_axis, 25], showticklabels=False, zeroline=False)
    )
    st.plotly_chart(fig_adm, use_container_width=True, config={'displayModeBar': False})

    pv_phenotype_html = """
<div class="custom-card pv-phenotype-card" style="border-left: 4px solid #475569; padding: 0.4rem 0.6rem; margin-top: 0.3rem; margin-bottom: 0;">
    <div class="title-text" style="color: #334155; font-size: 0.85rem;">🔬 Phase III: PV Loop Phenotyping</div>
    <p class="text-muted" style="font-size: 0.65rem; font-style: italic; margin-bottom: 4px;">Exploratory concept — CNN-LSTM reconstruction</p>

    <div style="background-color: #F8FAFC; border-radius: 6px; padding: 4px 6px; margin-bottom: 4px; border: 1px solid #E2E8F0;">
        <div style="font-weight: 700; color: #64748B; margin-bottom: 4px; font-size: 0.65rem; letter-spacing: 0.5px;">PHENOTYPE CLASSIFICATION LEGEND</div>
        <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4px 8px; font-size: 0.7rem;">
            <div style="color: #475569; text-align: center;">🟢 <b>Normal</b><br><span style="font-size: 0.65rem;">HMPP ✅ IBP ✅</span></div>
            <div style="color: #475569; text-align: center;">🔴 <b>Weakness</b><br><span style="font-size: 0.65rem;">HMPP ↓ IBP ✅</span></div>
            <div style="color: #475569; text-align: center;">⚠️ <b>Obstruction</b><br><span style="font-size: 0.65rem;">HMPP ✅ IBP ↑</span></div>
        </div>
    </div>

    <div style="font-size: 0.75rem; color: #1E293B;">
        <div style="font-weight: 600; border-bottom: 1px solid #E2E8F0; padding-bottom: 2px; margin-bottom: 4px;">ESTIMATED PHENOTYPE — Demo-001 (Simulated)</div>
        <div style="display: flex; justify-content: space-between; gap: 0.5rem; margin-bottom: 4px;">
            <span><b>HMPP:</b> ~145 mmHg <span style="color:#10B981;">✅ Normal</span></span>
        </div>
        <div style="display: flex; justify-content: space-between; gap: 0.5rem; margin-bottom: 4px;">
            <span><b>IBP:</b> Est. normal <span style="color:#10B981;">✅</span></span>
        </div>
        <div style="background-color: #ECFDF5; border: 1px solid #A7F3D0; color: #065F46; padding: 2px; border-radius: 4px; font-weight: bold; text-align: center; margin-bottom: 4px;">
            → 🟢 Functional Swallow
        </div>
    </div>

    <p class="text-muted" style="font-size: 0.65rem; text-align: center; margin-top: 2px; margin-bottom: 0; line-height: 1.2;">
        ⚠️ Requires Phase III validation + HRIM confirm
    </p>
</div>
"""
    st.html(pv_phenotype_html)
# ------------------------------------------
# 右欄：✨ AI Clinical Copilot 工作區 (互動式對話 + EMR 提交)
# ------------------------------------------
with col_right:
    # 1. 標題與警示區塊
    st.markdown("""
<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px;">
    <div class="title-text" style="color: #6D28D9; margin: 0;">
        <span style="font-size: 1.1em; margin-right: 4px;">✨</span> AI Clinical Copilot
    </div>
    <span style="font-size: 0.7rem; color: #64748B; font-style: italic;">Rule-based</span>
</div>
<div class="llm-disclaimer">
    <b>⚠️ DECISION SUPPORT ONLY:</b> AI responses do not constitute clinical diagnosis.
</div>
""", unsafe_allow_html=True)

    # 2. 動態對話歷史區塊 (從 session_state 渲染)
    def md_to_html(text: str) -> str:
        """Convert basic Markdown to HTML (bold, italic, tables, newlines).
        Works with pure regex — no extra dependencies, safe for cloud deploy."""
        lines = text.split("\n")
        result_lines = []
        table_buf = []

        def flush_table():
            if not table_buf:
                return
            html = '<table style="width:100%; border-collapse:collapse; font-size:0.7rem; margin:6px 0;">'
            for idx, row in enumerate(table_buf):
                cells = [c.strip() for c in row.strip("|").split("|")]
                # skip separator row (e.g. |---|---|)
                if all(re.match(r'^[:\-\s]+$', c) for c in cells):
                    continue
                tag = "th" if idx == 0 else "td"
                style_th = 'style="padding:3px 6px; border-bottom:2px solid #E2E8F0; color:#64748B; font-weight:600; text-align:center;"'
                style_td = 'style="padding:3px 6px; border-bottom:1px solid #F1F5F9; text-align:center;"'
                style = style_th if idx == 0 else style_td
                html += "<tr>" + "".join(f"<{tag} {style}>{c}</{tag}>" for c in cells) + "</tr>"
            html += "</table>"
            result_lines.append(html)
            table_buf.clear()

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                table_buf.append(stripped)
            else:
                flush_table()
                result_lines.append(line)
        flush_table()

        text = "\n".join(result_lines)
        # Bold: **text** → <b>text</b>
        text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
        # Italic: *text* → <i>text</i>  (but not ** which was already handled)
        text = re.sub(r'(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)', r'<i>\1</i>', text)
        # Newlines
        text = text.replace("\n", "<br>")
        return text

    def render_chat_message(msg):
        """Render a single chat message as styled HTML with Markdown support."""
        content_html = md_to_html(msg["content"])
        if msg["role"] == "ai":
            actions_html = ""
            if msg.get("actions"):
                action_spans = ""
                for a in msg["actions"]:
                    if "Flag" in a or "⚠" in a:
                        action_spans += f'<span style="border: 1px solid #FCA5A5; background: #FEF2F2; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; color: #991B1B; display: inline-block; margin-right: 4px;">{a}</span>'
                    else:
                        action_spans += f'<span style="border: 1px solid #CBD5E1; background: #F8FAFC; padding: 2px 6px; border-radius: 4px; font-size: 0.7rem; color: #475569; display: inline-block; margin-right: 4px;">{a}</span>'
                actions_html = f'<div style="margin-top: 8px;">{action_spans}</div>'
            return f"""
            <div style="background: #FFFFFF; border: 1px solid #DDD6FE; border-left: 3px solid #8B5CF6; padding: 8px 10px; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="font-size: 0.65rem; color: #64748B; margin-bottom: 6px; border-bottom: 1px solid #F1F5F9; padding-bottom: 4px;">
                    <b style="color: #6D28D9;">🤖 NCS-MIMO Agent</b> <span style="margin: 0 4px;">|</span> <i>AI-generated, not verified</i> <span style="float: right;">{msg['time']}</span>
                </div>
                <div style="font-size: 0.75rem; color: #334155; line-height: 1.5;">{content_html}</div>
                {actions_html}
            </div>"""
        else:
            return f"""
            <div style="background: #EFF6FF; border: 1px solid #BFDBFE; border-right: 3px solid #3B82F6; padding: 8px 10px; border-radius: 6px; margin-left: 15%; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
                <div style="font-size: 0.65rem; color: #64748B; margin-bottom: 6px; border-bottom: 1px solid #DBEAFE; padding-bottom: 4px; text-align: right;">
                    <span style="float: left;">{msg['time']}</span> <b style="color: #1D4ED8;">👨‍⚕️ Physician</b>
                </div>
                <div style="font-size: 0.75rem; color: #1E3A8A; line-height: 1.4; text-align: right;">{content_html}</div>
            </div>"""

    messages_html = ""
    # 1. 確保「思考中動畫」放在最前面（反轉後會在最底部）
    if st.session_state.thinking:
        messages_html += """
        <div style="background: #FFFFFF; border: 1px solid #DDD6FE; border-left: 3px solid #8B5CF6; padding: 10px 12px; border-radius: 6px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);">
            <div style="font-size: 0.65rem; color: #64748B; margin-bottom: 6px;">
                <b style="color: #6D28D9;">🤖 NCS-MIMO Agent</b> <span style="margin: 0 4px;">|</span> <i>Analyzing...</i>
            </div>
            <div style="display: flex; align-items: center; gap: 4px; padding: 4px 0;">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span style="font-size: 0.7rem; color: #8B5CF6; margin-left: 6px; font-style: italic;">Reviewing sensor data...</span>
            </div>
        </div>"""

    # 2. 將歷史對話反向 (reversed) 迭代加入
    for m in reversed(st.session_state.messages):
        messages_html += render_chat_message(m)

    chat_container_html = f"""
<div class="chat-container" style="height: 280px; overflow-y: auto; background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 10px; margin-bottom: 8px; display: flex; flex-direction: column-reverse; gap: 10px; box-shadow: inset 0 2px 4px rgba(0,0,0,0.02);">
    {messages_html}
</div>
"""
    st.html(chat_container_html)

    # 3. 建議 chips (自適應深淺色模式)
    st.markdown("<div style='font-size: 0.65rem; color: #64748B; margin-bottom: 4px;'>💡 Quick ask:</div>", unsafe_allow_html=True)
    chip_c1, chip_c2 = st.columns(2)
    with chip_c1:
        with st.container():
            st.markdown('<div class="quick-chip">', unsafe_allow_html=True)
            if st.button("🍽 Safe for oral feeding?", key="chip1", use_container_width=True):
                now_str = datetime.now().strftime("%I:%M %p")
                user_text = "Is this patient safe for oral feeding?"
                st.session_state.messages.append({"role": "user", "content": user_text, "actions": [], "time": now_str})
                # Show thinking indicator first
                st.session_state.thinking = True
                st.session_state._pending_query = user_text
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
    with chip_c2:
        with st.container():
            st.markdown('<div class="quick-chip">', unsafe_allow_html=True)
            if st.button("📊 Compare to yesterday", key="chip2", use_container_width=True):
                now_str = datetime.now().strftime("%I:%M %p")
                user_text = "Compare to yesterday"
                st.session_state.messages.append({"role": "user", "content": user_text, "actions": [], "time": now_str})
                st.session_state.thinking = True
                st.session_state._pending_query = user_text
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

    # 4. 使用者輸入框 (更明顯的樣式已在 CSS 中處理)
    user_input = st.chat_input("💬 Ask about this patient...", key="copilot_input")
    if user_input:
        now_str = datetime.now().strftime("%I:%M %p")
        st.session_state.messages.append({"role": "user", "content": user_input, "actions": [], "time": now_str})
        st.session_state.thinking = True
        st.session_state._pending_query = user_input
        st.rerun()

    # 4.5 處理 pending thinking → 生成回覆 (模擬 AI 思考延遲)
    if st.session_state.thinking and hasattr(st.session_state, '_pending_query'):
        time.sleep(1.8)  # 模擬思考時間
        query = st.session_state._pending_query
        now_str = datetime.now().strftime("%I:%M %p")
        resp = get_ai_response(query)
        st.session_state.messages.append({"role": "ai", "content": resp["text"], "actions": resp["actions"], "time": now_str})
        st.session_state.thinking = False
        del st.session_state._pending_query
        st.rerun()

    # 5. 病歷草稿 (Auto-generated EMR Draft)
    st.markdown("<hr style='margin: 4px 0 8px 0; border-color: #E2E8F0;'>", unsafe_allow_html=True)

    if not st.session_state.draft_discarded:
        if st.session_state.editing_draft:
            # --- 編輯模式 ---
            st.markdown("""
<div style="font-size: 0.65rem; font-weight: 700; color: #6D28D9; margin-bottom: 4px;">
    ✏️ Editing EMR Draft
</div>""", unsafe_allow_html=True)
            edited_text = st.text_area(
                "Edit draft",
                value=st.session_state.draft_text,
                height=160,
                label_visibility="collapsed",
                key="draft_editor",
            )
            save_c1, save_c2 = st.columns(2)
            with save_c1:
                if st.button("💾 Save", type="primary", use_container_width=True, key="save_draft"):
                    st.session_state.draft_text = edited_text
                    st.session_state.editing_draft = False
                    st.rerun()
            with save_c2:
                if st.button("↩ Cancel", use_container_width=True, key="cancel_edit"):
                    st.session_state.editing_draft = False
                    st.rerun()
        else:
            # --- 檢視模式 ---
            draft_display = st.session_state.draft_text.replace("\n", "<br>")
            draft_note_html = f"""
<div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 8px; padding: 8px 10px; margin-bottom: 8px; box-shadow: 0 1px 2px rgba(0,0,0,0.05); position: relative;">
    <div style="position: absolute; top: -8px; left: 10px; background: #FFFFFF; padding: 0 6px; font-size: 0.65rem; font-weight: 700; color: #6D28D9; border: 1px solid #E2E8F0; border-radius: 4px;">
        📄 Auto-generated EMR Draft
    </div>
    <div style="font-size: 0.7rem; color: #334155; line-height: 1.4; margin-top: 6px;">
        {draft_display}
    </div>
</div>
"""
            st.html(draft_note_html)

            # 6. 提交 / 編輯 / 捨棄 按鈕
            bc1, bc2, bc3 = st.columns([4, 2, 2])
            with bc1:
                if st.button("✔ Accept as Note", type="primary", use_container_width=True, key="accept_btn"):
                    st.session_state.emr_sent = True
                    st.rerun()
            with bc2:
                if st.button("✏ Edit", use_container_width=True, key="edit_btn"):
                    st.session_state.editing_draft = True
                    st.rerun()
            with bc3:
                if st.button("✖ Discard", use_container_width=True, key="discard_btn"):
                    st.session_state.draft_discarded = True
                    st.session_state.emr_sent = False
                    st.rerun()

        # 7. 成功送出提示
        if st.session_state.emr_sent:
            st.markdown("""
<div style="background-color: #D1FAE5; border: 1px solid #10B981; color: #065F46; padding: 0.4rem 0.6rem; border-radius: 6px; font-size: 0.8rem; margin-top: 4px; width: 100%; box-sizing: border-box; text-align: center;">
    ✓ Draft sent to EMR (needs sign-off)
</div>
""", unsafe_allow_html=True)
    else:
        # 草稿已捨棄的狀態
        st.markdown("""
<div style="background-color: #FEF2F2; border: 1px solid #FECACA; color: #991B1B; padding: 0.4rem 0.6rem; border-radius: 6px; font-size: 0.8rem; margin-top: 4px; width: 100%; box-sizing: border-box; text-align: center;">
    ✖ Draft discarded
</div>
""", unsafe_allow_html=True)
        if st.button("🔄 Restore Draft", use_container_width=True, key="restore_btn"):
            st.session_state.draft_discarded = False
            st.session_state.draft_text = DEFAULT_EMR_DRAFT
            st.rerun()