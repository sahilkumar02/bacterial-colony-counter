import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import io
import hashlib
from datetime import datetime

st.set_page_config(page_title="AI Colony Counter & Strain Phenotyping Suite", page_icon="🔬", layout="wide", initial_sidebar_state="expanded")

if "history_archive" not in st.session_state:
    st.session_state.history_archive = []
if "show_history_panel" not in st.session_state:
    st.session_state.show_history_panel = False
if "selected_history_id" not in st.session_state:
    st.session_state.selected_history_id = None

st.markdown("""
<style>
    html, body, [class*="css"] { font-size: 17px !important; color: #f8fafc !important; }
    .stApp { background: radial-gradient(circle at center, #0f172a 0%, #020617 100%) !important; color: #f8fafc !important; overflow-x: hidden; }

    /* Sidebar High-Contrast Dark Styling */
    section[data-testid="stSidebar"] {
        background: #0b1120 !important;
        border-right: 1px solid rgba(56, 189, 248, 0.3) !important;
    }
    section[data-testid="stSidebar"] * {
        color: #f1f5f9 !important;
    }

    /* Fix All Labels, Subheaders, Markdown & Widget Text Visibility */
    label, p, span, h1, h2, h3, h4, .stMarkdown, [data-testid="stWidgetLabel"] p {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }

    /* File Uploader Box & Browse Button Visibility Fix */
    [data-testid="stFileUploader"] {
        background: rgba(15, 23, 42, 0.85) !important;
        border: 2px dashed #38bdf8 !important;
        border-radius: 16px !important;
        padding: 16px !important;
    }
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(30, 41, 59, 0.9) !important;
        border-radius: 12px !important;
        color: #f8fafc !important;
    }
    [data-testid="stFileUploaderDropzone"] div,
    [data-testid="stFileUploaderDropzone"] span,
    [data-testid="stFileUploaderDropzone"] small {
        color: #e2e8f0 !important;
    }
    [data-testid="stFileUploaderDropzone"] button {
        background: linear-gradient(90deg, #0284c7, #38bdf8) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 700 !important;
        padding: 8px 18px !important;
        border-radius: 8px !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.5) !important;
    }

    /* Buttons & Download Buttons Visibility Fix */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #0284c7, #2563eb) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        padding: 10px 16px !important;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.3) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #38bdf8, #34d399) !important;
        color: #020617 !important;
    }

    /* Expander & Number Input Visibility Fix */
    [data-testid="stExpander"] {
        background: rgba(15, 23, 42, 0.85) !important;
        border: 1px solid rgba(56, 189, 248, 0.35) !important;
        border-radius: 12px !important;
    }
    input {
        color: #ffffff !important;
        background-color: #1e293b !important;
    }

    /* Center Glowing Holographic Microscope Watermark */
    .microscope-watermark {
        position: fixed;
        top: 54%;
        left: 55%;
        transform: translate(-50%, -50%);
        width: 340px;
        height: 340px;
        opacity: 0.22;
        pointer-events: none;
        z-index: 0;
        animation: pulseGlow 4s infinite ease-in-out;
    }
    @keyframes pulseGlow {
        0%, 100% { filter: drop-shadow(0 0 18px #38bdf8) drop-shadow(0 0 40px #0284c7); transform: translate(-50%, -50%) scale(1); }
        50% { filter: drop-shadow(0 0 32px #22d3ee) drop-shadow(0 0 65px #34d399); transform: translate(-50%, -50%) scale(1.04); }
    }

    /* Multi-Color Animated Floating Bacteria */
    .bacteria-bg { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; pointer-events: none; z-index: 0; overflow: hidden; }
    .bacterium { position: absolute; border-radius: 50px; opacity: 0.22; animation: floatBacteria 18s infinite ease-in-out; }
    .b1 { width: 48px; height: 18px; background: #38bdf8; box-shadow: 0 0 12px #38bdf8; top: 15%; left: 10%; animation-duration: 16s; }
    .b2 { width: 32px; height: 32px; background: #34d399; box-shadow: 0 0 12px #34d399; top: 70%; left: 20%; animation-duration: 21s; border-radius: 50%; }
    .b3 { width: 55px; height: 20px; background: #a855f7; box-shadow: 0 0 12px #a855f7; top: 30%; left: 80%; animation-duration: 19s; }
    .b4 { width: 28px; height: 28px; background: #f472b6; box-shadow: 0 0 12px #f472b6; top: 80%; left: 75%; animation-duration: 15s; border-radius: 50%; }
    .b5 { width: 42px; height: 16px; background: #fbbf24; box-shadow: 0 0 12px #fbbf24; top: 50%; left: 45%; animation-duration: 23s; }
    .b6 { width: 36px; height: 14px; background: #22d3ee; box-shadow: 0 0 12px #22d3ee; top: 12%; left: 60%; animation-duration: 17s; }
    @keyframes floatBacteria {
        0% { transform: translate(0px, 0px) rotate(0deg); }
        33% { transform: translate(35px, -45px) rotate(120deg); }
        66% { transform: translate(-25px, 30px) rotate(240deg); }
        100% { transform: translate(0px, 0px) rotate(360deg); }
    }

    /* Header & Metric Cards */
    .lab-header { background: rgba(15, 23, 42, 0.88); border: 1.5px solid #38bdf8; border-radius: 16px; padding: 20px 24px; margin-bottom: 16px; box-shadow: 0 0 25px rgba(56, 189, 248, 0.2); }
    .lab-title { font-size: 28px !important; font-weight: 800; color: #38bdf8 !important; text-shadow: 0 0 12px rgba(56, 189, 248, 0.4); margin: 0; }
    .lab-subtitle { font-size: 16px !important; color: #e2e8f0 !important; margin-top: 6px; }
    .metric-card { background: rgba(15, 23, 42, 0.9); border: 1px solid #38bdf8; border-radius: 14px; padding: 16px; text-align: center; box-shadow: 0 0 15px rgba(56, 189, 248, 0.15); margin-bottom: 10px; }
    .metric-label { font-size: 14px !important; color: #bae6fd !important; font-weight: 700; text-transform: uppercase; }
    .metric-value { font-size: 26px !important; font-weight: 800; color: #34d399 !important; margin-top: 4px; text-shadow: 0 0 10px rgba(52, 211, 153, 0.4); }
</style>

<div class="bacteria-bg">
    <div class="bacterium b1"></div><div class="bacterium b2"></div><div class="bacterium b3"></div>
    <div class="bacterium b4"></div><div class="bacterium b5"></div><div class="bacterium b6"></div>
</div>

<div class="microscope-watermark">
    <svg viewBox="0 0 24 24" fill="none" stroke="#38bdf8" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round">
        <path d="M6 18h8"/>
        <path d="M3 22h18"/>
        <path d="M14 22a7 7 0 1 0 0-14h-1"/>
        <path d="M9 14h2"/>
        <path d="M9 12a2 2 0 0 1-2-2V6h6v4a2 2 0 0 1-2 2Z"/>
        <path d="M12 6V3a1 1 0 0 0-1-1H9a1 1 0 0 0-1 1v3"/>
        <circle cx="10" cy="18" r="1.5" fill="#34d399"/>
    </svg>
</div>
""", unsafe_allow_html=True)

# Top Header & Quick History Icon Button
h_col1, h_col2 = st.columns([4, 1])
with h_col1:
    st.markdown("""
    <div class="lab-header">
        <div class="lab-title">🔬 AI-Powered Colony Counter & Strain Phenotyping Suite</div>
        <div class="lab-subtitle">Developed by <b>Sahil Kumar</b> | Automated OpenCV Segmentation, Phenotype Profiling & CFU/mL Analytics</div>
    </div>
    """, unsafe_allow_html=True)
with h_col2:
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    history_count = len(st.session_state.history_archive)
    if st.button(f"🕒 History ({history_count})", use_container_width=True, help="View all uploaded photos & results"):
        st.session_state.show_history_panel = not st.session_state.show_history_panel

def classify_phenotype(rgb_color):
    r, g, b = rgb_color
    if r > 180 and g > 180 and b > 170:
        return "Cream / Off-White (Standard)"
    elif r > 170 and g > 140 and b < 110:
        return "Golden / Yellow (S. aureus)"
    elif r > 160 and g < 110 and b < 110:
        return "Red / Pink Pigmented (Serratia)"
    elif g > r + 15 and g > b + 15:
        return "Blue-Green (Pseudomonas)"
    elif r < 95 and g < 95 and b < 95:
        return "Dark / Melanized"
    return "Translucent / Mucoid"

def extract_colony_record(cnt, colony_idx, gray, img_rgb, annotated):
    area = cv2.contourArea(cnt)
    perimeter = cv2.arcLength(cnt, True)
    circularity = (4 * np.pi * area / (perimeter ** 2)) if perimeter > 0 else 0
    M = cv2.moments(cnt)
    cx = int(M["m10"] / M["m00"]) if M["m00"] != 0 else 0
    cy = int(M["m01"] / M["m00"]) if M["m00"] != 0 else 0
    c_mask = np.zeros(gray.shape, dtype=np.uint8)
    cv2.drawContours(c_mask, [cnt], -1, 255, -1)
    mean_val = cv2.mean(img_rgb, mask=c_mask)[:3]
    rgb_tuple = (int(mean_val[0]), int(mean_val[1]), int(mean_val[2]))
    phenotype = classify_phenotype(rgb_tuple)
    cv2.drawContours(annotated, [cnt], -1, (52, 211, 153), 2)
    cv2.putText(annotated, str(colony_idx), (cx - 8, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (250, 204, 21), 2)
    return {"Colony ID": colony_idx, "X (px)": cx, "Y (px)": cy, "Area (px²)": round(area, 2), "Circularity": round(circularity, 3), "Mean RGB": str(rgb_tuple), "Strain Phenotype": phenotype}

def process_plate_image(pil_image, threshold_val, min_area, max_area, blur_val, invert_mode, use_roi, roi_scale, use_watershed):
    img_rgb = np.array(pil_image.convert("RGB"))
    h, w, _ = img_rgb.shape
    annotated = img_rgb.copy()
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    blur_val = blur_val + 1 if blur_val % 2 == 0 else blur_val
    blurred = cv2.GaussianBlur(gray, (blur_val, blur_val), 0)
    thresh_type = cv2.THRESH_BINARY_INV if invert_mode else cv2.THRESH_BINARY
    _, binary = cv2.threshold(blurred, threshold_val, 255, thresh_type)
    if use_roi:
        mask = np.zeros((h, w), dtype=np.uint8)
        center = (w // 2, h // 2)
        radius = int((min(h, w) // 2) * (roi_scale / 100.0))
        cv2.circle(mask, center, radius, 255, -1)
        binary = cv2.bitwise_and(binary, binary, mask=mask)
        cv2.circle(annotated, center, radius, (56, 189, 248), 3)
    kernel = np.ones((3, 3), np.uint8)
    opening = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=2)
    colonies_data = []
    colony_idx = 0
    if use_watershed:
        sure_bg = cv2.dilate(opening, kernel, iterations=3)
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, 0.35 * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)
        unknown = cv2.subtract(sure_bg, sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0
        markers = cv2.watershed(img_rgb, markers)
        for m in np.unique(markers):
            if m <= 1:
                continue
            comp_mask = np.uint8(markers == m) * 255
            contours, _ = cv2.findContours(comp_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                if min_area <= cv2.contourArea(cnt) <= max_area:
                    colony_idx += 1
                    colonies_data.append(extract_colony_record(cnt, colony_idx, gray, img_rgb, annotated))
    else:
        contours, _ = cv2.findContours(opening, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for cnt in contours:
            if min_area <= cv2.contourArea(cnt) <= max_area:
                colony_idx += 1
                colonies_data.append(extract_colony_record(cnt, colony_idx, gray, img_rgb, annotated))
    return Image.fromarray(annotated), pd.DataFrame(colonies_data)

def image_to_bytes(pil_img):
    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    return buf.getvalue()

# Sidebar Controls
with st.sidebar:
    st.markdown("## 🧬 Lab Navigation")
    nav_choice = st.radio("Select Workspace Mode:", ["🔬 Analyze New Plate", "🕒 History Archive (" + str(len(st.session_state.history_archive)) + ")"])
    st.markdown("---")
    st.markdown("### 🎛️ Lab Control Panel")
    with st.expander("🔬 Detection & Sensitivity", expanded=True):
        threshold_val = st.slider("Threshold Sensitivity", 10, 255, 125)
        min_area = st.slider("Min Colony Size (px²)", 5, 250, 20)
        max_area = st.slider("Max Colony Size (px²)", 200, 12000, 3000)
        blur_val = st.slider("Noise Reduction (Blur)", 1, 15, 5, step=2)
        invert_mode = st.checkbox("Dark Colonies on Light Agar", value=False)
    with st.expander("🧫 Petri Dish ROI & Segmentation", expanded=True):
        use_roi = st.checkbox("Enable Circular ROI Mask", value=True)
        roi_scale = st.slider("Petri Dish ROI Radius (%)", 50, 100, 88)
        use_watershed = st.checkbox("Watershed Clump Splitting", value=True)
    with st.expander("🧪 CFU/mL Calculator Parameters", expanded=True):
        dilution_exp = st.number_input("Dilution Factor Exponent (10^-x)", min_value=0, max_value=15, value=4)
        volume_plated = st.number_input("Volume Plated (mL)", min_value=0.01, max_value=5.0, value=0.1, step=0.05)
        manual_offset = st.number_input("Manual Count Override (+/-)", min_value=-500, max_value=500, value=0)

def render_history_drawer():
    st.markdown("### 🕒 Uploaded Photos History & Results Archive")
    if not st.session_state.history_archive:
        st.info("Abhi tak koi photo upload nahi hui hai. Jaise hi aap photo upload karenge, uska result yahan automatically save ho jayega.")
    else:
        if st.button("🗑️ Clear All History"):
            st.session_state.history_archive = []
            st.rerun()
        for record in st.session_state.history_archive:
            with st.expander(f"🧫 {record['filename']}  |  CFU: {record['total_cfu']}  |  {record['cfu_ml']} CFU/mL  |  🕒 {record['timestamp']}", expanded=True):
                r_col1, r_col2 = st.columns([1, 1.3])
                r_col1.image(record["annotated_bytes"], caption=f"Annotated: {record['filename']}", use_container_width=True)
                with r_col2:
                    st.markdown(f"**📄 File Name:** `{record['filename']}`")
                    st.markdown(f"**⏰ Upload Time:** `{record['timestamp']}`")
                    st.markdown(f"**📐 Image Resolution:** `{record['resolution']}`")
                    st.markdown(f"**🧫 Total Colonies (CFU):** `{record['total_cfu']}`")
                    st.markdown(f"**🧪 Concentration:** `{record['cfu_ml']} CFU/mL`")
                    st.markdown(f"**🧬 Dominant Strain:** `{record['dominant_strain']}`")
                    st.markdown(f"**⚙️ Settings Used:** `{record['settings']}`")
                    if not record["df"].empty:
                        st.dataframe(record["df"].head(8), use_container_width=True, hide_index=True)
                    b1, b2 = st.columns(2)
                    b1.download_button("📥 Download CSV", record["csv_bytes"], f"{record['filename']}_colonies.csv", "text/csv", key=f"csv_{record['id']}", use_container_width=True)
                    b2.download_button("🖼️ Download PNG", record["annotated_bytes"], f"{record['filename']}_annotated.png", "image/png", key=f"png_{record['id']}", use_container_width=True)

# If Top History Icon is toggled ON or Sidebar History Mode is selected
if st.session_state.show_history_panel or nav_choice.startswith("🕒 History Archive"):
    render_history_drawer()
    st.markdown("---")

if nav_choice == "🔬 Analyze New Plate":
    uploaded_file = st.file_uploader("📤 Upload Agar Plate Image (JPG, PNG, JPEG)", type=["jpg", "jpeg", "png"])
    if uploaded_file is not None:
        raw_image = Image.open(uploaded_file)
        annotated_img, df_results = process_plate_image(raw_image, threshold_val, min_area, max_area, blur_val, invert_mode, use_roi, roi_scale, use_watershed)
        final_count = max(0, len(df_results) + manual_offset)
        dilution_factor = 10 ** (-dilution_exp)
        cfu_per_ml = (final_count / (dilution_factor * volume_plated)) if (dilution_factor * volume_plated) > 0 else 0
        avg_area = round(df_results["Area (px²)"].mean(), 1) if not df_results.empty else 0.0
        dominant_strain = df_results["Strain Phenotype"].mode()[0].split("(")[0].strip() if not df_results.empty else "N/A"

        csv_data = df_results.to_csv(index=False).encode("utf-8")
        png_bytes = image_to_bytes(annotated_img)
        clean_name = uploaded_file.name.rsplit(".", 1)[0]

        # Auto-Save or Update Current Upload in History Archive
        signature = f"{uploaded_file.name}_{threshold_val}_{min_area}_{max_area}_{invert_mode}_{roi_scale}_{use_watershed}_{manual_offset}"
        rec_id = hashlib.md5(signature.encode()).hexdigest()[:8]
        existing_ids = [item["id"] for item in st.session_state.history_archive]
        if rec_id not in existing_ids:
            st.session_state.history_archive.insert(0, {
                "id": rec_id,
                "timestamp": datetime.now().strftime("%d %b %Y, %I:%M:%S %p"),
                "filename": clean_name,
                "resolution": f"{raw_image.width}x{raw_image.height} px",
                "total_cfu": final_count,
                "cfu_ml": f"{cfu_per_ml:.2e}",
                "dominant_strain": dominant_strain,
                "settings": f"Thresh: {threshold_val} | Area: {min_area}-{max_area} | ROI: {roi_scale}%",
                "annotated_bytes": png_bytes,
                "csv_bytes": csv_data,
                "df": df_results.copy()
            })

        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f'<div class="metric-card"><div class="metric-label">Total Colonies (CFU)</div><div class="metric-value">{final_count}</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-label">Concentration (CFU/mL)</div><div class="metric-value">{cfu_per_ml:.2e}</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-label">Avg Colony Area</div><div class="metric-value">{avg_area} px²</div></div>', unsafe_allow_html=True)
        c4.markdown(f'<div class="metric-card"><div class="metric-label">Dominant Phenotype</div><div class="metric-value" style="font-size:20px !important;">{dominant_strain}</div></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_img1, col_img2 = st.columns(2)
        with col_img1:
            st.subheader("🧫 Original Agar Plate")
            st.image(raw_image, use_container_width=True)
        with col_img2:
            st.subheader("🎯 AI Annotated Detection")
            st.image(annotated_img, use_container_width=True)

        st.markdown("---")
        st.subheader("📊 Strain Phenotyping & Morphometric Log")
        if not df_results.empty:
            pheno_counts = df_results["Strain Phenotype"].value_counts().reset_index()
            pheno_counts.columns = ["Strain Phenotype", "Colony Count"]
            p_col1, p_col2 = st.columns([1, 2])
            p_col1.dataframe(pheno_counts, use_container_width=True, hide_index=True)
            p_col2.dataframe(df_results, use_container_width=True, hide_index=True)
        else:
            st.info("No colonies detected with current settings. Adjust sliders in the Lab Control Panel.")

        st.markdown("### 💾 Export Results")
        exp_col1, exp_col2 = st.columns(2)
        exp_col1.download_button("📥 Download Colony CSV", csv_data, f"{clean_name}_colonies.csv", "text/csv", use_container_width=True)
        exp_col2.download_button("🖼️ Download Annotated PNG", png_bytes, f"{clean_name}_annotated.png", "image/png", use_container_width=True)
    else:
        st.info("👆 Upload a Petri dish / agar plate photo above to start automated counting. Every upload is automatically saved in 🕒 History!")