import io
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

# 2. High-Contrast Bio-Lab CSS + Animated Bacteria + Watermark
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Inter:wght@400;500;600&display=swap');

/* Deep Bio-Lab Dark Background */
.stApp {
    background: radial-gradient(circle at 15% 20%, #09192f 0%, #040b16 55%, #02060d 100%) !important;
    font-family: 'Inter', sans-serif;
    color: #F8FAFC !important;
}

/* Keep content above animated background */
[data-testid="stAppViewContainer"] > .main {
    position: relative;
    z-index: 2;
}

/* Force High-Contrast Colors on ALL Streamlit Text & Labels */
h1, h2, h3, h4, p, span, div, label {
    color: #F1F5F9;
}

/* Special Glowing Colors for Widget Labels */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    color: #38BDF8 !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    letter-spacing: 0.3px;
}

/* Sidebar Styling & Bright Text */
[data-testid="stSidebar"] {
    background-color: rgba(8, 16, 32, 0.94) !important;
    backdrop-filter: blur(14px);
    border-right: 1px solid rgba(56, 189, 248, 0.25);
    z-index: 3;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #34D399 !important;
}

/* Expander Header Styling */
[data-testid="stExpander"] {
    background-color: rgba(15, 23, 42, 0.85) !important;
    border: 1px solid rgba(56, 189, 248, 0.3) !important;
    border-radius: 12px !important;
}

[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {
    color: #FBBF24 !important;
    font-weight: 600 !important;
}

/* Checkbox Label */
[data-testid="stCheckbox"] label p {
    color: #34D399 !important;
    font-weight: 500 !important;
}

/* File Uploader Box Fix (No more white-on-white text!) */
[data-testid="stFileUploader"] section {
    background-color: rgba(15, 23, 42, 0.88) !important;
    border: 1.5px dashed #38BDF8 !important;
    border-radius: 14px !important;
    padding: 16px !important;
}

[data-testid="stFileUploader"] section span,
[data-testid="stFileUploader"] section small,
[data-testid="stFileUploader"] section div {
    color: #E2E8F0 !important;
}

[data-testid="stFileUploader"] button {
    background-color: #0284C7 !important;
    color: #FFFFFF !important;
    border: none !important;
    font-weight: 600 !important;
}

/* Tabs Text Color */
button[data-baseweb="tab"] p {
    color: #CBD5E1 !important;
    font-weight: 600 !important;
}
button[data-baseweb="tab"][aria-selected="true"] p {
    color: #38BDF8 !important;
}

/* Floating Bacteria Container */
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
    opacity: 0.42;
    filter: blur(0.4px);
    animation: swim linear infinite;
}

.bacillus {
    width: 48px;
    height: 16px;
    border-radius: 20px;
}

.coccus {
    width: 22px;
    height: 22px;
    border-radius: 50%;
}

.diplococcus {
    width: 34px;
    height: 18px;
    border-radius: 12px;
    border-style: dashed !important;
}

.c-cyan {
    background: rgba(56, 189, 248, 0.28);
    border: 2px solid #38BDF8;
    box-shadow: 0 0 18px rgba(56, 189, 248, 0.65);
}
.c-green {
    background: rgba(52, 211, 153, 0.28);
    border: 2px solid #34D399;
    box-shadow: 0 0 18px rgba(52, 211, 153, 0.65);
}
.c-purple {
    background: rgba(192, 132, 252, 0.28);
    border: 2px solid #C084FC;
    box-shadow: 0 0 18px rgba(192, 132, 252, 0.65);
}
.c-amber {
    background: rgba(251, 191, 36, 0.28);
    border: 2px solid #FBBF24;
    box-shadow: 0 0 18px rgba(251, 191, 36, 0.65);
}
.c-pink {
    background: rgba(244, 114, 182, 0.28);
    border: 2px solid #F472B6;
    box-shadow: 0 0 18px rgba(244, 114, 182, 0.65);
}

@keyframes swim {
    0% { transform: translateY(110vh) translateX(0px) rotate(0deg); }
    50% { transform: translateY(50vh) translateX(45px) rotate(180deg); }
    100% { transform: translateY(-15vh) translateX(-30px) rotate(360deg); }
}

/* Starting Hero Banner */
.hero-card {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.88) 0%, rgba(30, 41, 59, 0.78) 100%);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(56, 189, 248, 0.4);
    border-radius: 18px;
    padding: 26px 30px;
    margin-bottom: 22px;
    box-shadow: 0 10px 35px rgba(0, 0, 0, 0.5);
}

.hero-badge {
    display: inline-block;
    background: rgba(52, 211, 153, 0.18);
    color: #34D399 !important;
    border: 1px solid rgba(52, 211, 153, 0.45);
    padding: 4px 12px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.8px;
    margin-bottom: 10px;
}

.hero-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 32px;
    font-weight: 700;
    background: linear-gradient(90deg, #38BDF8, #34D399, #C084FC);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0 0 8px 0;
}

.hero-sub {
    color: #E2E8F0 !important;
    font-size: 15px;
    margin: 0;
    line-height: 1.5;
}

/* Result Cards */
.result-card {
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(12px);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 14px;
    padding: 18px 14px;
    text-align: center;
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.4);
}

.res-icon { font-size: 22px; margin-bottom: 6px; }
.res-value {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 28px;
    font-weight: 700;
    margin: 2px 0;
}
.res-label {
    font-size: 12px;
    color: #CBD5E1 !important;
    text-transform: uppercase;
    letter-spacing: 0.8px;
}

/* Start Feature Cards */
.start-grid-card {
    background: rgba(15, 23, 42, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(56, 189, 248, 0.25);
    border-radius: 14px;
    padding: 20px;
    margin-bottom: 12px;
}

/* Permanent Floating Watermark */
.sahil-watermark {
    position: fixed;
    bottom: 14px;
    left: 16px;
    z-index: 9999;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(56, 189, 248, 0.45);
    padding: 6px 14px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 600;
    color: #38BDF8 !important;
    letter-spacing: 0.6px;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.45);
    pointer-events: none;
}
.sahil-watermark span {
    color: #34D399 !important;
}
</style>

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
<div class="bacterium coccus c-amber" style="left: 31%; animation-duration: 24s; animation-delay: 7s;"></div>
<div class="bacterium bacillus c-cyan" style="left: 67%; animation-duration: 23s; animation-delay: 8s;"></div>
</div>

<div class="sahil-watermark">🧬 Created by <span>Sahil Kumar</span></div>

<div class="hero-card">
<div class="hero-badge">🧬 AUTOMATED MICROBIOLOGY VISION SUITE</div>
<h1 class="hero-title">BioCount AI — Bacterial Colony Counter</h1>
<p class="hero-sub">Created by <b style="color:#34D399;">Sahil Kumar</b> • High-precision OpenCV colony segmentation, morphological sizing, and automated CFU/mL calculation.</p>
</div>
""", unsafe_allow_html=True)

# 3. Sidebar Parameters
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

# 4. File Uploader
uploaded_file = st.file_uploader("📤 Upload Petri Dish Image (JPG, PNG, JPEG)", type=["jpg", "jpeg", "png"])

# 5. Starting Screen
if uploaded_file is None:
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("""
<div class="start-grid-card">
<h4 style="color:#38BDF8; margin-top:0;">🎯 Smart Dish Isolation</h4>
<p style="color:#E2E8F0; font-size:14px; margin-bottom:0;">Automatically masks out plastic petri dish rims and glare artifacts to count only valid agar colonies.</p>
</div>
""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
<div class="start-grid-card">
<h4 style="color:#34D399; margin-top:0;">🧬 Morphology & Sizing</h4>
<p style="color:#E2E8F0; font-size:14px; margin-bottom:0;">Classifies detected colonies into Small, Medium, and Large phenotypes with exact pixel radius & area.</p>
</div>
""", unsafe_allow_html=True)
    with c3:
        st.markdown("""
<div class="start-grid-card">
<h4 style="color:#C084FC; margin-top:0;">🧪 Instant CFU/mL Math</h4>
<p style="color:#E2E8F0; font-size:14px; margin-bottom:0;">Calculates viable microbial concentration in scientific notation and exports lab-ready CSV & PNG reports.</p>
</div>
""", unsafe_allow_html=True)

# 6. Main Processing & Results
else:
    file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
    img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    h, w = img_rgb.shape[:2]

    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)

    thresh_type = cv2.THRESH_BINARY_INV if invert_mode else cv2.THRESH_BINARY
    _, thresh = cv2.threshold(blurred, threshold_val, 255, thresh_type)

    # Circular ROI Masking
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
                ring_color = (56, 189, 248)   # Cyan
            elif area < 500:
                size_class = "Medium (Circular)"
                ring_color = (52, 211, 153)   # Green
            else:
                size_class = "Large (Spreading)"
                ring_color = (251, 191, 36)   # Amber

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

    # Stamp Watermark on Annotated Image
    font_scale = max(0.5, w / 1100.0)
    cv2.putText(
        annotated_img,
        "Created by Sahil Kumar | BioCount AI",
        (16, h - 18),
        cv2.FONT_HERSHEY_SIMPLEX,
        font_scale,
        (56, 189, 248),
        2,
        cv2.LINE_AA
    )

    total_colonies = len(colonies_data)
    dilution_factor = 10 ** dilution_exp
    cfu_ml = (total_colonies * dilution_factor) / plating_vol if plating_vol > 0 else 0

    # Glowing Result Summary Cards
    r1, r2, r3, r4 = st.columns(4)
    with r1:
        st.markdown(f"""
<div class="result-card">
<div class="res-icon">🦠</div>
<div class="res-value" style="color:#38BDF8;">{total_colonies}</div>
<div class="res-label">Detected Colonies</div>
</div>
""", unsafe_allow_html=True)
    with r2:
        st.markdown(f"""
<div class="result-card">
<div class="res-icon">🧪</div>
<div class="res-value" style="color:#34D399;">{cfu_ml:.2e}</div>
<div class="res-label">Concentration (CFU/mL)</div>
</div>
""", unsafe_allow_html=True)
    with r3:
        st.markdown(f"""
<div class="result-card">
<div class="res-icon">🔬</div>
<div class="res-value" style="color:#C084FC;">10⁻{dilution_exp}</div>
<div class="res-label">Dilution Factor</div>
</div>
""", unsafe_allow_html=True)
    with r4:
        avg_sz = round(np.mean([c["Area (px²)"] for c in colonies_data]), 1) if total_colonies > 0 else 0
        st.markdown(f"""
<div class="result-card">
<div class="res-icon">📐</div>
<div class="res-value" style="color:#FBBF24;">{avg_sz}</div>
<div class="res-label">Avg Area (px²)</div>
</div>
""", unsafe_allow_html=True)

    st.write("")

    # Result Tabs
    tab1, tab2, tab3 = st.tabs(["📸 Visual Overlay", "📊 Phenotype Analytics", "📥 Export Report"])

    with tab1:
        st.markdown("<p style='color:#38BDF8; font-weight:600;'>Color Legend: 🔵 Cyan = Small | 🟢 Green = Medium | 🟡 Amber = Large</p>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("<h4 style='color:#CBD5E1;'>Original Plate</h4>", unsafe_allow_html=True)
            st.image(img_rgb, use_container_width=True)
        with col2:
            st.markdown("<h4 style='color:#34D399;'>AI Detected Overlay</h4>", unsafe_allow_html=True)
            st.image(annotated_img, use_container_width=True)

    with tab2:
        if total_colonies > 0:
            df = pd.DataFrame(colonies_data)
            c_chart1, c_chart2 = st.columns(2)
            with c_chart1:
                st.markdown("<h4 style='color:#38BDF8;'>Colony Count by Phenotype</h4>", unsafe_allow_html=True)
                st.bar_chart(df["Phenotype"].value_counts())
            with c_chart2:
                st.markdown("<h4 style='color:#34D399;'>Area Distribution (px²)</h4>", unsafe_allow_html=True)
                st.area_chart(df["Area (px²)"])
        else:
            st.warning("No colonies detected. Try adjusting the Threshold Sensitivity in the sidebar.")

    with tab3:
        if total_colonies > 0:
            df = pd.DataFrame(colonies_data)
            st.dataframe(df, use_container_width=True)

            dl1, dl2 = st.columns(2)
            with dl1:
                csv_bytes = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📄 Download CSV Data",
                    data=csv_bytes,
                    file_name="biocount_colony_data.csv",
                    mime="text/csv"
                )
            with dl2:
                pil_annotated = Image.fromarray(annotated_img)
                buf = io.BytesIO()
                pil_annotated.save(buf, format="PNG")
                st.download_button(
                    "🖼️ Download Annotated Plate (PNG)",
                    data=buf.getvalue(),
                    file_name="biocount_annotated_plate.png",
                    mime="image/png"
                )
        else:
            st.info("Upload an image with detectable colonies to export reports.")
