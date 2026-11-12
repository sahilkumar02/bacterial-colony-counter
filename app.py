import io
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

# 2. Session State for History
if "history" not in st.session_state:
    st.session_state["history"] = []
if "view_history_idx" not in st.session_state:
    st.session_state["view_history_idx"] = None
if "last_processed_file" not in st.session_state:
    st.session_state["last_processed_file"] = None

# 3. High-Contrast CSS + Glowing Microscope + Larger Typography
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@600;700&family=Inter:wght@400;500;600;700&display=swap');

.stApp {
    background: radial-gradient(circle at 20% 15%, #0b213f 0%, #050d1a 55%, #02060d 100%) !important;
    font-family: 'Inter', sans-serif;
    color: #F8FAFC !important;
}

[data-testid="stAppViewContainer"] > .main {
    position: relative;
    z-index: 2;
}

/* Glowing Center Microscope Watermark */
.center-microscope-glow {
    position: fixed;
    top: 54%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 310px;
    height: 310px;
    opacity: 0.22;
    pointer-events: none;
    z-index: 1;
    filter: drop-shadow(0 0 22px #38BDF8) drop-shadow(0 0 48px #34D399);
    animation: pulseGlow 4s ease-in-out infinite alternate;
}

@keyframes pulseGlow {
    0% { opacity: 0.16; filter: drop-shadow(0 0 18px #38BDF8) drop-shadow(0 0 35px #34D399); }
    100% { opacity: 0.28; filter: drop-shadow(0 0 28px #38BDF8) drop-shadow(0 0 60px #34D399); }
}

/* Floating Multi-Color Bacteria Background */
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
    opacity: 0.45;
    animation: swim linear infinite;
}

.bacillus { width: 54px; height: 18px; border-radius: 20px; }
.coccus { width: 24px; height: 24px; border-radius: 50%; }
.diplococcus { width: 38px; height: 20px; border-radius: 12px; border-style: dashed !important; }

.c-cyan { background: rgba(56, 189, 248, 0.3); border: 2px solid #38BDF8; box-shadow: 0 0 20px rgba(56, 189, 248, 0.75); }
.c-green { background: rgba(52, 211, 153, 0.3); border: 2px solid #34D399; box-shadow: 0 0 20px rgba(52, 211, 153, 0.75); }
.c-purple { background: rgba(192, 132, 252, 0.3); border: 2px solid #C084FC; box-shadow: 0 0 20px rgba(192, 132, 252, 0.75); }
.c-amber { background: rgba(251, 191, 36, 0.3); border: 2px solid #FBBF24; box-shadow: 0 0 20px rgba(251, 191, 36, 0.75); }
.c-pink { background: rgba(244, 114, 182, 0.3); border: 2px solid #F472B6; box-shadow: 0 0 20px rgba(244, 114, 182, 0.75); }

@keyframes swim {
    0% { transform: translateY(110vh) translateX(0px) rotate(0deg); }
    50% { transform: translateY(50vh) translateX(45px) rotate(180deg); }
    100% { transform: translateY(-15vh) translateX(-30px) rotate(360deg); }
}

/* Fix All Text & Widget Colors */
[data-testid="stSidebar"] {
    background-color: #071122 !important;
    border-right: 1px solid rgba(56, 189, 248, 0.35);
    z-index: 3;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3,
[data-testid="stSidebar"] p {
    color: #34D399 !important;
}

/* Fix White Expander Header Bug */
[data-testid="stExpander"] {
    background-color: #0F172A !important;
    border: 1px solid #38BDF8 !important;
    border-radius: 12px !important;
}

[data-testid="stExpander"] summary {
    background-color: #1E293B !important;
    border-radius: 10px !important;
    padding: 8px 12px !important;
}

[data-testid="stExpander"] summary span,
[data-testid="stExpander"] summary p {
    color: #FBBF24 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
}

/* Slider & Input Labels */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: #38BDF8 !important;
    font-weight: 600 !important;
    font-size: 15px !important;
}

/* Checkbox Text */
[data-testid="stCheckbox"] label p {
    color: #F8FAFC !important;
    font-weight: 600 !important;
    font-size: 15px !important;
}

/* Radio Navigation Buttons Fix */
[data-testid="stRadio"] > div {
    background: rgba(15, 23, 42, 0.9);
    padding: 10px 16px;
    border-radius: 14px;
    border: 1px solid rgba(56, 189, 248, 0.4);
}

[data-testid="stRadio"] label p {
    color: #F8FAFC !important;
    font-size: 17px !important;
    font-weight: 700 !important;
}

/* File Uploader & Browse Button Fix */
[data-testid="stFileUploader"] section {
    background-color: rgba(15, 23, 42, 0.92) !important;
    border: 2px dashed #38BDF8 !important;
    border-radius: 16px !important;
    padding: 20px !important;
}

[data-testid="stFileUploader"] section div,
[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small {
    color: #F1F5F9 !important;
    font-size: 15px !important;
}

[data-testid="stFileUploader"] button {
    background: linear-gradient(90deg, #0284C7, #0D9488) !important;
    color: #FFFFFF !important;
    border: 1px solid #38BDF8 !important;
    font-weight: 700 !important;
    font-size: 15px !important;
    padding: 8px 18px !important;
}

/* Hero Banner (Larger Text) */
.hero-card {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.92) 0%, rgba(30, 41, 59, 0.85) 100%);
    backdrop-filter: blur(16px);
    border: 1.5px solid rgba(56, 189, 248, 0.5);
    border-radius: 20px;
    padding: 30px 32px;
    margin-bottom: 22px;
    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.55);
}

.hero-badge {
    display: inline-block;
    background: rgba(52, 211, 153, 0.2);
    color: #34D399 !important;
    border: 1px solid #34D399;
    padding: 5px 14px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.8px;
    margin-bottom: 12px;
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 36px;
    font-weight: 700;
    background: linear-gradient(90deg, #38BDF8, #34D399, #C084FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 10px 0;
    line-height: 1.2;
}

.hero-sub {
    color: #F1F5F9 !important;
    font-size: 17px;
    margin: 0;
    line-height: 1.6;
}

/* Feature & Info Cards (Larger to fill space cleanly) */
.info-card {
    background: rgba(15, 23, 42, 0.88);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 16px;
    padding: 24px 22px;
    margin-bottom: 16px;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.45);
}

.info-card h3 {
    margin: 0 0 10px 0;
    font-size: 20px;
    font-family: 'Space Grotesk', sans-serif;
}

.info-card p, .info-card li {
    color: #E2E8F0 !important;
    font-size: 15.5px;
    line-height: 1.6;
    margin-bottom: 6px;
}

/* Result Metric Cards */
.result-card {
    background: rgba(15, 23, 42, 0.9);
    border: 1.5px solid rgba(56, 189, 248, 0.4);
    border-radius: 16px;
    padding: 22px 14px;
    text-align: center;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.45);
}

.res-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 32px;
    font-weight: 700;
}

.res-label {
    font-size: 13px;
    color: #E2E8F0 !important;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* Bottom Footer Banner & Floating Watermark */
.bottom-footer {
    margin-top: 32px;
    background: linear-gradient(90deg, rgba(15, 23, 42, 0.92), rgba(14, 116, 144, 0.25), rgba(15, 23, 42, 0.92));
    border: 1px solid rgba(56, 189, 248, 0.35);
    border-radius: 16px;
    padding: 20px 24px;
    text-align: center;
}

.sahil-watermark {
    position: fixed;
    bottom: 14px;
    left: 16px;
    z-index: 9999;
    background: rgba(7, 17, 34, 0.94);
    border: 1.5px solid #38BDF8;
    padding: 7px 16px;
    border-radius: 999px;
    font-size: 13px;
    font-weight: 700;
    color: #38BDF8 !important;
    box-shadow: 0 0 18px rgba(56, 189, 248, 0.4);
    pointer-events: none;
}
.sahil-watermark span { color: #34D399 !important; }
</style>

<!-- Glowing Neon Microscope Watermark in Center -->
<div class="center-microscope-glow">
<svg viewBox="0 0 24 24" fill="none" stroke="#38BDF8" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round">
<path d="M6 18h8"/>
<path d="M3 22h18"/>
<path d="M14 22a7 7 0 1 0 0-14h-1"/>
<path d="M9 14h2"/>
<path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/>
<path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>
<circle cx="15" cy="15" r="1.5" stroke="#34D399"/>
</svg>
</div>

<!-- Animated Multi-Color Bacteria Background -->
<div class="bio-bg">
<div class="bacterium bacillus c-cyan" style="left: 5%; animation-duration: 18s; animation-delay: 0s;"></div>
<div class="bacterium coccus c-green" style="left: 16%; animation-duration: 14s; animation-delay: 2s;"></div>
<div class="bacterium bacillus c-purple" style="left: 28%; animation-duration: 21s; animation-delay: 1s;"></div>
<div class="bacterium diplococcus c-amber" style="left: 40%; animation-duration: 16s; animation-delay: 4s;"></div>
<div class="bacterium coccus c-pink" style="left: 52%; animation-duration: 19s; animation-delay: 2s;"></div>
<div class="bacterium bacillus c-green" style="left: 64%; animation-duration: 15s; animation-delay: 3s;"></div>
<div class="bacterium coccus c-cyan" style="left: 75%; animation-duration: 20s; animation-delay: 0.5s;"></div>
<div class="bacterium bacillus c-pink" style="left: 86%; animation-duration: 17s; animation-delay: 5s;"></div>
<div class="bacterium diplococcus c-purple" style="left: 92%; animation-duration: 22s; animation-delay: 1.5s;"></div>
</div>

<div class="sahil-watermark">🧬 Created by <span>Sahil Kumar</span></div>

<div class="hero-card">
<div class="hero-badge">🔬 AUTOMATED MICROBIOLOGY & BIOINFORMATICS SUITE</div>
<h1 class="hero-title">BioCount AI — Bacterial Colony Counter</h1>
<p class="hero-sub">Created by <b style="color:#34D399;">Sahil Kumar</b> • High-precision OpenCV colony segmentation, morphological sizing, CFU/mL calculation, and instant plate history archive.</p>
</div>
""", unsafe_allow_html=True)

# 4. Top Navigation Mode Switcher
nav_choice = st.radio(
    "Navigation Mode",
    ["🔬 Analyze New Plate", f"📜 Plate History Archive ({len(st.session_state['history'])})"],
    horizontal=True,
    label_visibility="collapsed"
)

# 5. Function to Render Full Report
def display_full_report(record):
    st.markdown(f"<h3 style='color:#38BDF8; font-size:24px;'>📋 Analysis Report: {record['filename']}</h3>", unsafe_allow_html=True)
    st.markdown(f"<p style='color:#CBD5E1; font-size:15px;'>⏱️ Timestamp: <b>{record['timestamp']}</b> &nbsp;|&nbsp; 🧪 Dilution: <b>10⁻{record['dilution_exp']}</b> &nbsp;|&nbsp; 💧 Plated Vol: <b>{record['plating_vol']} mL</b></p>", unsafe_allow_html=True)

    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""<div class="result-card"><div class="res-value" style="color:#38BDF8;">{record['total_colonies']}</div><div class="res-label">Detected Colonies</div></div>""", unsafe_allow_html=True)
    with r2:
        st.markdown(f"""<div class="result-card"><div class="res-value" style="color:#34D399;">{record['cfu_ml']:.2e}</div><div class="res-label">Concentration (CFU/mL)</div></div>""", unsafe_allow_html=True)
    with r3:
        st.markdown(f"""<div class="result-card"><div class="res-value" style="color:#C084FC;">10⁻{record['dilution_exp']}</div><div class="res-label">Dilution Factor</div></div>""", unsafe_allow_html=True)
    with r4:
        avg_sz = round(np.mean([c["Area (px²)"] for c in record['colonies_data']]), 1) if record['total_colonies'] > 0 else 0
        st.markdown(f"""<div class="result-card"><div class="res-value" style="color:#FBBF24;">{avg_sz}</div><div class="res-label">Avg Area (px²)</div></div>""", unsafe_allow_html=True)

    st.write("")
    tab1, tab2, tab3 = st.tabs(["📸 Visual Overlay", "📊 Phenotype Analytics", "📥 Export & Reports"])

    with tab1:
        st.markdown("<p style='color:#38BDF8; font-size:16px; font-weight:700;'>Ring Color Code: 🔵 Cyan = Small | 🟢 Green = Medium | 🟡 Amber = Large</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h4 style='color:#F8FAFC; font-size:18px;'>Original Agar Plate</h4>", unsafe_allow_html=True)
            st.image(record['img_rgb'], use_container_width=True)
        with col2:
            st.markdown("<h4 style='color:#34D399; font-size:18px;'>AI Segmented Overlay</h4>", unsafe_allow_html=True)
            st.image(record['annotated_img'], use_container_width=True)

    with tab2:
        if record['total_colonies'] > 0:
            df = pd.DataFrame(record['colonies_data'])
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("<h4 style='color:#38BDF8;'>Colonies by Phenotype</h4>", unsafe_allow_html=True)
                st.bar_chart(df["Phenotype"].value_counts())
            with c2:
                st.markdown("<h4 style='color:#34D399;'>Colony Area Distribution (px²)</h4>", unsafe_allow_html=True)
                st.area_chart(df["Area (px²)"])
        else:
            st.warning("No colonies detected within current threshold limits.")

    with tab3:
        if record['total_colonies'] > 0:
            df = pd.DataFrame(record['colonies_data'])
            st.dataframe(df, use_container_width=True)
            dl1, dl2 = st.columns(2)
            with dl1:
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button("📄 Download CSV Report", data=csv_bytes, file_name=f"{record['filename']}_report.csv", mime="text/csv", key=f"csv_{record['id']}")
            with dl2:
                pil_annotated = Image.fromarray(record['annotated_img'])
                buf = io.BytesIO()
                pil_annotated.save(buf, format="PNG")
                st.download_button("🖼️ Download Annotated Image (PNG)", data=buf.getvalue(), file_name=f"{record['filename']}_annotated.png", mime="image/png", key=f"png_{record['id']}")


# ==========================================
# MODE 1: ANALYZE NEW PLATE
# ==========================================
if nav_choice == "🔬 Analyze New Plate":
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
        # Top 3 Feature Cards
        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown("""<div class="info-card"><h3 style="color:#38BDF8;">🎯 Smart Dish Isolation</h3><p>Automatically masks plastic petri dish edges and light reflections so only valid microbial colonies on the agar surface are counted.</p></div>""", unsafe_allow_html=True)
        with c2:
            st.markdown("""<div class="info-card"><h3 style="color:#34D399;">🧬 Phenotype Classification</h3><p>Segments individual colonies and classifies them into <b>Small (Punctiform)</b>, <b>Medium (Circular)</b>, and <b>Large (Spreading)</b> morphologies.</p></div>""", unsafe_allow_html=True)
        with c3:
            st.markdown("""<div class="info-card"><h3 style="color:#C084FC;">📜 1-Click History Archive</h3><p>Every scanned agar plate is automatically logged with its timestamp, CFU/mL result, and visual overlay for instant recall anytime.</p></div>""", unsafe_allow_html=True)

        # Bottom Detailed Lab Protocol & Reference Section (Fills bottom space meaningfully)
        b1, b2 = st.columns(2)
        with b1:
            st.markdown("""
<div class="info-card">
<h3 style="color:#FBBF24;">🧪 Standard Microbiology Counting Protocol</h3>
<ul>
<li><b>Step 1 — Capture Clear Plate Photo:</b> Place the petri dish against a uniform contrasting background with minimal glare.</li>
<li><b>Step 2 — Calibrate Threshold:</b> Use the left sidebar sliders to match colony contrast and filter out tiny agar bubbles.</li>
<li><b>Step 3 — Set Serial Dilution:</b> Enter your dilution exponent (e.g., 10⁻⁵) and inoculum volume (typically 0.1 mL) for automatic CFU/mL calculation.</li>
<li><b>Statistically Valid Range:</b> Standard microbiology guidelines recommend plates containing <b>30 to 300 colonies</b> for accurate CFU estimation.</li>
</ul>
</div>
""", unsafe_allow_html=True)
        with b2:
            st.markdown("""
<div class="info-card">
<h3 style="color:#F472B6;">🧫 Colony Phenotype & Morphology Reference</h3>
<ul>
<li><b style="color:#38BDF8;">🔵 Small / Punctiform (&lt; 120 px²):</b> Pinpoint colonies typical of slow-growing or high-density bacterial cultures.</li>
<li><b style="color:#34D399;">🟢 Medium / Circular (120 – 500 px²):</b> Well-isolated, uniform round colonies ideal for pure culture sub-culturing.</li>
<li><b style="color:#FBBF24;">🟡 Large / Spreading (&gt; 500 px²):</b> Broad or mucoid colonies often seen in motile strains or nutrient-rich agar media.</li>
<li><b>Formula Applied:</b> <code>CFU/mL = (Colony Count × 10^Dilution) / Plated Volume (mL)</code></li>
</ul>
</div>
""", unsafe_allow_html=True)

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
                 