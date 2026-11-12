import io
import time
from datetime import datetime
import cv2
import numpy as np
import pandas as pd
from PIL import Image
import streamlit as st

# 1. Page Configuration
st.set_page_config(
    page_title="BioCount AI | Sahil Kumar",
    page_icon="🧫",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. Session State Initialization for History Tracking
if "history" not in st.session_state:
    st.session_state["history"] = []

if "view_history_idx" not in st.session_state:
    st.session_state["view_history_idx"] = None

if "last_processed_file" not in st.session_state:
    st.session_state["last_processed_file"] = None

# 3. High-Contrast CSS + Floating Bacteria + Center Microscope Watermark
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

.stApp {
    background: radial-gradient(circle at 15% 20%, #09192f 0%, #040b16 55%, #02060d 100%) !important;
    font-family: 'Inter', sans-serif;
    color: #F8FAFC !important;
}

[data-testid="stAppViewContainer"] > .main {
    position: relative;
    z-index: 2;
}

/* Center Microscope Watermark */
.center-microscope-watermark {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-size: 260px;
    opacity: 0.05;
    pointer-events: none;
    z-index: 1;
    user-select: none;
    filter: drop-shadow(0 0 50px rgba(56, 189, 248, 0.5));
}

/* Floating Bacteria Background */
.bio-bg {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
    z-index: 0;
    pointer-events: none;
}

.bacterium {
    position: absolute;
    opacity: 0.38;
    filter: blur(0.5px);
    animation: swim linear infinite;
}

.bacillus { width: 48px; height: 16px; border-radius: 20px; }
.coccus { width: 22px; height: 22px; border-radius: 50%; }
.diplococcus { width: 34px; height: 18px; border-radius: 12px; border-style: dashed !important; }

.c-cyan { background: rgba(56, 189, 248, 0.28); border: 2px solid #38BDF8; box-shadow: 0 0 18px rgba(56, 189, 248, 0.65); }
.c-green { background: rgba(52, 211, 153, 0.28); border: 2px solid #34D399; box-shadow: 0 0 18px rgba(52, 211, 153, 0.65); }
.c-purple { background: rgba(192, 132, 252, 0.28); border: 2px solid #C084FC; box-shadow: 0 0 18px rgba(192, 132, 252, 0.65); }
.c-amber { background: rgba(251, 191, 36, 0.28); border: 2px solid #FBBF24; box-shadow: 0 0 18px rgba(251, 191, 36, 0.65); }
.c-pink { background: rgba(244, 114, 182, 0.28); border: 2px solid #F472B6; box-shadow: 0 0 18px rgba(244, 114, 182, 0.65); }

@keyframes swim {
    0% { transform: translateY(110vh) translateX(0px) rotate(0deg); }
    50% { transform: translateY(50vh) translateX(45px) rotate(180deg); }
    100% { transform: translateY(-15vh) translateX(-30px) rotate(360deg); }
}

/* Sidebar & Form Labels */
[data-testid="stSidebar"] {
    background-color: rgba(8, 16, 32, 0.94) !important;
    backdrop-filter: blur(14px);
    border-right: 1px solid rgba(56, 189, 248, 0.25);
    z-index: 3;
}

[data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] label {
    color: #38BDF8 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
}

[data-testid="stExpander"] {
    background-color: rgba(15, 23, 42, 0.85) !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 12px !important;
}

[data-testid="stExpander"] summary span {
    color: #FBBF24 !important;
    font-weight: 600 !important;
}

[data-testid="stFileUploader"] section {
    background-color: rgba(15, 23, 42, 0.88) !important;
    border: 1.5px dashed #38BDF8 !important;
    border-radius: 14px !important;
}

[data-testid="stFileUploader"] section div, [data-testid="stFileUploader"] section span {
    color: #E2E8F0 !important;
}

/* Hero Header & Watermarks */
.hero-card {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.88) 0%, rgba(30, 41, 59, 0.78) 100%);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(56, 189, 248, 0.4);
    border-radius: 18px;
    padding: 24px 28px;
    margin-bottom: 20px;
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.5);
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(90deg, #38BDF8, #34D399, #C084FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 6px 0;
}

.result-card {
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 14px;
    padding: 18px 12px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

.res-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px;
    font-weight: 700;
}

.res-label {
    font-size: 12px;
    color: #CBD5E1 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

.sahil-watermark {
    position: fixed;
    bottom: 14px;
    left: 16px;
    z-index: 9999;
    background: rgba(15, 23, 42, 0.88);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(56, 189, 248, 0.45);
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    color: #38BDF8 !important;
    letter-spacing: 0.6px;
    pointer-events: none;
}
.sahil-watermark span { color: #34D399 !important; }

/* History Table Card */
.history-item-card {
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
</style>

<!-- Floating Microscope Watermark in Center -->
<div class="center-microscope-watermark">🔬</div>

<!-- Animated Multi-Color Bacteria in Background -->
<div class="bio-bg">
<div class="bacterium bacillus c-cyan" style="left: 6%; animation-duration: 18s; animation-delay: 0s;"></div>
<div class="bacterium coccus c-green" style="left: 15%; animation-duration: 14s; animation-delay: 3s;"></div>
<div class="bacterium bacillus c-purple" style="left: 26%; animation-duration: 22s; animation-delay: 1s;"></div>
<div class="bacterium diplococcus c-amber" style="left: 38%; animation-duration: 16s; animation-delay: 5s;"></div>
<div class="bacterium coccus c-pink" style="left: 49%; animation-duration: 19s; animation-delay: 2s;"></div>
<div class="bacterium bacillus c-green" style="left: 61%; animation-duration: 15s; animation-delay: 4s;"></div>
<div class="bacterium coccus c-cyan" style="left: 72%; animation-duration: 21s; animation-delay: 0.5s;"></div>
<div class="bacterium bacillus c-pink" style="left: 83%; animation-duration: 17s; animation-delay: 6s;"></div>
<div class="bacterium diplococcus c-purple" style="left: 91%; animation-duration: 20s; animation-delay: 2.5s;"></div>
</div>

<div class="sahil-watermark">🧬 Created by <span>Sahil Kumar</span></div>

<div class="hero-card">
<h1 class="hero-title">BioCount AI — Bacterial Colony Counter</h1>
<p style="color:#CBD5E1; margin:0;">Created by <b style="color:#34D399;">Sahil Kumar</b> • Automated Colony Enumeration, Sizing & Instant Plate History Archive</p>
</div>
""", unsafe_allow_html=True)

# 4. Top Navigation Bar (Switch between Live Scanner and Plate History)
nav_choice = st.radio(
    "Select Mode",
    ["🔬 Analyze New Plate", f"📜 Plate History Archive ({len(st.session_state['history'])})"],
    horizontal=True,
    label_visibility="collapsed"
)

# 5. Helper Function to Render Detailed Results
def display_full_report(record):
    st.markdown(f"### 📋 Plate Report: `{record['filename']}`")
    st.caption(f"Analyzed on: {record['timestamp']} | Parameters: Dilution 10⁻{record['dilution_exp']}, Vol: {record['plating_vol']} mL")

    # Metrics
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""
<div class="result-card">
<div class="res-value" style="color:#38BDF8;">{record['total_colonies']}</div>
<div class="res-label">Detected Colonies</div>
</div>
""", unsafe_allow_html=True)
    with r2:
        st.markdown(f"""
<div class="result-card">
<div class="res-value" style="color:#34D399;">{record['cfu_ml']:.2e}</div>
<div class="res-label">Concentration (CFU/mL)</div>
</div>
""", unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
<div class="result-card">
<div class="res-value" style="color:#C084FC;">10⁻{record['dilution_exp']}</div>
<div class="res-label">Dilution Factor</div>
</div>
""", unsafe_allow_html=True)
    with r4:
        avg_sz = round(np.mean([c["Area (px²)"] for c in record['colonies_data']]), 1) if record['total_colonies'] > 0 else 0
        st.markdown(f"""
<div class="result-card">
<div class="res-value" style="color:#FBBF24;">{avg_sz}</div>
<div class="res-label">Avg Area (px²)</div>
</div>
""", unsafe_allow_html=True)

    st.write("")
    tab1, tab2, tab3 = st.tabs(["📸 Visual Overlay", "📊 Phenotype Analytics", "📥 Export & Reports"])

    with tab1:
        st.markdown("<p style='color:#38BDF8; font-weight:600;'>Color Legend: 🔵 Cyan = Small | 🟢 Green = Medium | 🟡 Amber = Large</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h4 style='color:#CBD5E1;'>Original Plate</h4>", unsafe_allow_html=True)
            st.image(record['img_rgb'], use_container_width=True)
        with col2:
            st.markdown("<h4 style='color:#34D399;'>AI Detected Overlay</h4>", unsafe_allow_html=True)
            st.image(record['annotated_img'], use_container_width=True)

    with tab2:
        if record['total_colonies'] > 0:
            df = pd.DataFrame(record['colonies_data'])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<h4 style='color:#38BDF8;'>Colonies by Phenotype</h4>", unsafe_allow_html=True)
                st.bar_chart(df["Phenotype"].value_counts())
            with c2:
                st.markdown("<h4 style='color:#34D399;'>Area Distribution (px²)</h4>", unsafe_allow_html=True)
                st.area_chart(df["Area (px²)"])
        else:
            st.warning("No colonies detected within parameters.")

    with tab3:
        if record['total_colonies'] > 0:
            df = pd.DataFrame(record['colonies_data'])
            st.dataframe(df, use_container_width=True)
            dl1, dl2 = st.columns(2)
            with dl1:
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button("📄 Download CSV Data", data=csv_bytes, file_name=f"{record['filename']}_report.csv", mime="text/csv", key=f"csv_{record['id']}")
            with dl2:
                pil_annotated = Image.fromarray(record['annotated_img'])
                buf = io.BytesIO()
                pil_annotated.save(buf, format="PNG")
                st.download_button("🖼️ Download Annotated Plate (PNG)", data=buf.getvalue(), file_name=f"{record['filename']}_annotated.png", mime="image/png", key=f"png_{record['id']}")


# ==========================================
# MODE 1: ANALYZE NEW PLATE
# ==========================================
if nav_choice == "🔬 Analyze New Plate":
    # Sidebar
    with st.sidebar:
        st.markdown("### 🎛️ Lab Control Panel")
        with st.expander("🔬 Detection & Sensitivity", expanded=True):
            threshold_val = st.slider("Threshold Sensitivity", 10, 255, 125)
            min_area = st.slider("Min Colony Size (px²)", 5, 250, 20)
            max_area = st.slider("Max Colony Size (px²)", 200, 12000, 3000)
            blur_val = st.slider("Noise Reduction (Blur)", 1, 15, 5, step=2)
            invert_mode = st.checkbox("Dark Colonies on Light Agar", value=True)

        with st.expander("🧪 Dilution & CFU/mL Setup", expanded=True):
            dilution_exp = st.number_input("Dilution Exponent (10⁻ˣ)", min_value=0, max_value=12, value=5, step=1)
            plating_vol = st.number_input("Plated Volume (mL)", min_value=0.01, max_value=5.0, value=0.1, step=0.05)

    uploaded_file = st.file_uploader("📤 Upload Petri Dish Image (JPG, PNG, JPEG)", type=["jpg", "jpeg", "png"])

    if uploaded_file is None:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="result-card"><h4 style="color:#38BDF8; margin:0 0 6px 0;">🎯 Smart Masking</h4><p style="color:#CBD5E1; font-size:13px; margin:0;">Auto-masks petri rims & glare to count agar colonies only.</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class="result-card"><h4 style="color:#34D399; margin:0 0 6px 0;">🧬 Phenotyping</h4><p style="color:#CBD5E1; font-size:13px; margin:0;">Categorizes into Small, Medium, and Large phenotypes.</p></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class="result-card"><h4 style="color:#C084FC; margin:0 0 6px 0;">📜 History Tracking</h4><p style="color:#CBD5E1; font-size:13px; margin:0;">Auto-logs past uploads with 1-click reload access.</p></div>""", unsafe_allow_html=True)
    else:
        file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
        img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        h, w = img_rgb.shape[:2]

        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)
        thresh_type = cv2.THRESH_BINARY_INV if invert_mode else cv2.THRESH_BINARY
        _, thresh = cv2.threshold(blurred, threshold_val, 255, thresh_type)

        mask = np.zeros((h, w), dtype=np.uint8)
        center = (int(w / 2), int(h / 2))
        radius = int(min(w, h) * 0.46)
        cv2.circle(mask, center, radius, 255, -1)
        masked_thresh = cv2.bitwise_and(thresh, thresh, mask=mask)

        contours, _ = cv2.findContours(masked_thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        annotated_img = img_rgb.copy()
        cv2.circle(annotated_img, center, radius, (56, 189, 248), 3)

        colonies_data = []
        cid = 1

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if min_area <= area <= max_area:
                ((x, y), r) = cv2.minEnclosingCircle(cnt)
                if area < 120:
                    size_class = "Small (Punctiform)"
                    ring_color = (56, 189, 248)
                elif area < 500:
                    size_class = "Medium (Circular)"
                    ring_color = (52, 211, 153)
                else:
                    size_class = "Large (Spreading)"
                    ring_color = (251, 191, 36)

                cv2.circle(annotated_img, (int(x), int(y)), int(r) + 3, ring_color, 2)
                cv2.circle(annotated_img, (int(x), int(y)), 2, (244, 114, 182), -1)

                colonies_data.append({
                    "ID": cid,
                    "Phenotype": size_class,
                    "X": int(x),
                    "Y": int(y),
                    "Radius (px)": round(r, 2),
                    "Area (px²)": round(area, 2)
                })
                cid += 1

        # Stamp watermark
        font_scale = max(0.5, w / 1100.0)
        cv2.putText(annotated_img, "Created by Sahil Kumar | BioCount AI", (16, h - 18), cv2.FONT_HERSHEY_SIMPLEX, font_scale, (56, 189, 248), 2, cv2.LINE_AA)

        total_colonies = len(colonies_data)
        dilution_factor = 10 ** dilution_exp
        cfu_ml = (total_colonies * dilution_factor) / plating_vol if plating_vol > 0 else 0

        # Save to History (if new upload)
        file_signature = f"{uploaded_file.name}_{uploaded_file.size}"
        if st.session_state["last_processed_file"] != file_signature:
            record_entry = {
                "id": len(st.session_state["history"]) + 1,
                "filename": uploaded_file.name,
                "timestamp": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
                "img_rgb": img_rgb,
                "annotated_img": annotated_img,
                "colonies_data": colonies_data,
                "total_colonies": total_colonies,
                "dilution_exp": dilution_exp,
                "plating_vol": plating_vol,
                "cfu_ml": cfu_ml
            }
            st.session_state["history"].insert(0, record_entry)
            st.session_state["last_processed_file"] = file_signature

        # Display Current Results
        display_full_report(st.session_state["history"][0])


# ==========================================
# MODE 2: PLATE HISTORY ARCHIVE & PAST SEARCHES
# ==========================================
else:
    st.markdown("### 📜 Past Plate Analysis History")
    
    if len(st.session_state["history"]) == 0:
        st.info("No plates analyzed in this session yet. Upload a petri dish in 'Analyze New Plate' mode to see history here.")
    else:
        # History Table View
        col_list, col_preview = st.columns([1.1, 1.9])
        
        with col_list:
            st.markdown("#### 📁 Uploaded Plates")
            for idx, item in enumerate(st.session_state["history"]):
                with st.container():
                    st.markdown(f"""
<div style="background:rgba(15,23,42,0.9); border:1px solid rgba(56,189,248,0.3); border-radius:10px; padding:12px; margin-bottom:10px;">
    <div style="font-weight:700; color:#38BDF8; font-size:15px;">#{item['id']} {item['filename']}</div>
    <div style="color:#94A3B8; font-size:12px; margin:3px 0 6px 0;">⏱️ {item['timestamp']}</div>
    <div style="color:#34D399; font-weight:600; font-size:13px;">🦠 Colonies: {item['total_colonies']} &nbsp;|&nbsp; 🧪 {item['cfu_ml']:.2e} CFU/mL</div>
</div>
""", unsafe_allow_html=True)
                    if st.button(f"🔍 View Full Result", key=f"hist_btn_{item['id']}"):
                        st.session_state["view_history_idx"] = idx

        with col_preview:
            # Show either selected record or the most recent one
            sel_idx = st.session_state["view_history_idx"] if st.session_state["view_history_idx"] is not None else 0
            if 0 <= sel_idx < len(st.session_state["history"]):
                selected_item = st.session_state["history"][sel_idx]
                display_full_report(selected_item)
