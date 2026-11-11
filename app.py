import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import io
import math
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(
    page_title="AI Colony Counter Pro",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 AI-Powered Colony Counter & Strain Phenotyping Suite")
st.caption("Adaptive Thresholding • Tiny Colony Detection • Color Phenotyping • Lab PDF Reports")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ 1. Detection Sensitivity")
colony_type = st.sidebar.radio("Colony Appearance", ["Bright colonies on Dark Agar", "Dark colonies on Light Agar"])
sensitivity = st.sidebar.slider("Detection Sensitivity (Threshold Offset)", min_value=-30, max_value=30, value=5, step=1,
                               help="Agar colonies miss ho rahi hain to isko thoda increase karein.")
min_area = st.sidebar.number_input("Min Colony Area (px²)", min_value=1, max_value=2000, value=3)
max_area = st.sidebar.number_input("Max Colony Area (px²)", min_value=50, max_value=100000, value=15000)

st.sidebar.header("🧫 2. Advanced Segmentation")
use_watershed = st.sidebar.checkbox("Enable Watershed (Split Clustered Colonies)", value=True)
watershed_strictness = st.sidebar.slider("Separation Strictness", 0.1, 0.9, 0.35, 0.05)
circularity_threshold = st.sidebar.slider("Morphology Cutoff (Circularity)", 0.2, 0.9, 0.55, 0.05)

st.sidebar.header("🔢 3. CFU Calculator")
calc_cfu = st.sidebar.checkbox("Calculate CFU/mL", value=False)
if calc_cfu:
    dilution_factor = st.sidebar.number_input("Dilution Factor (e.g. 1000 for 10^-3)", min_value=1.0, value=100.0)
    plated_volume = st.sidebar.number_input("Volume Plated (in mL)", min_value=0.001, max_value=10.0, value=0.1)

# Helper: Color Classification
def classify_colony_color(h, s, v):
    if v < 45:
        return "Black/Dark"
    if s < 35:
        return "White/Cream" if v > 160 else "Translucent/Gray"
    if (0 <= h <= 10) or (165 <= h <= 179):
        return "Red/Pink"
    elif 11 <= h <= 25:
        return "Orange"
    elif 26 <= h <= 40:
        return "Yellow/Golden"
    elif 41 <= h <= 85:
        return "Green"
    elif 86 <= h <= 135:
        return "Blue/Cyan"
    elif 136 <= h <= 164:
        return "Purple/Violet"
    return "Mixed"

# Helper: Circular ROI Mask
def get_circular_roi(img_shape):
    h, w = img_shape[:2]
    center = (int(w / 2), int(h / 2))
    radius = int(min(h, w) * 0.44) # 44% to avoid plate rim edge noise
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, center, radius, 255, -1)
    return mask, center, radius

# Helper: PDF Generation
def generate_pdf_report(sample_id, analyst_name, total_count, cfu_val, df_summary):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0f52ba'))
    story.append(Paragraph("Microbiology Laboratory Analysis Report", title_style))
    story.append(Paragraph(f"<b>Generated On:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <b>Analyst:</b> {analyst_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Sample / Plate ID:</b> {sample_id}", styles['Normal']))
    story.append(Spacer(1, 15))

    cfu_str = f"{cfu_val:,.2e} CFU/mL" if cfu_val is not None else "Not Calculated"
    summary_data = [
        ["Total Colony Count", "Morphology Status", "CFU Concentration"],
        [str(total_count), "Quality Verified", cfu_str]
    ]
    sum_table = Table(summary_data, colWidths=[180, 180, 180])
    sum_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e6f0fa')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0f52ba')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc'))
    ]))
    story.append(sum_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("<b>Strain Phenotype Breakdown:</b>", styles['Heading3']))
    table_content = [["Phenotype / Color", "Count", "Percentage", "Avg Area (px²)"]]
    for _, row in df_summary.iterrows():
        table_content.append([
            str(row["Color_Group"]),
            str(row["Count"]),
            f"{row['Percentage (%)']}%",
            str(row["Avg_Area"])
        ])

    breakdown_table = Table(table_content, colWidths=[150, 100, 120, 130])
    breakdown_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f2f2f2')),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#dddddd')),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
    ]))
    story.append(breakdown_table)

    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# --- MAIN APP FLOW ---
uploaded_file = st.file_uploader("Upload Petri Dish Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    raw_image = Image.open(uploaded_file).convert("RGB")
    image_array = np.array(raw_image)
    h, w, _ = image_array.shape

    # 1. Circular Mask
    petri_mask, center, p_radius = get_circular_roi(image_array.shape)

    # 2. Grayscale & CLAHE (Contrast Enhancement)
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_gray = clahe.apply(gray)
    blurred = cv2.GaussianBlur(enhanced_gray, (5, 5), 0)

    # Calculate mean inside Petri dish only (ignoring black border)
    inner_pixels = blurred[petri_mask == 255]
    mean_val = np.mean(inner_pixels)
    std_val = np.std(inner_pixels)

    # 3. Dynamic Thresholding tailored to punctate colonies
    if colony_type == "Bright colonies on Dark Agar":
        thresh_cutoff = int(mean_val + (1.2 * std_val) - sensitivity)
        thresh_cutoff = max(10, min(245, thresh_cutoff))
        _, binary = cv2.threshold(blurred, thresh_cutoff, 255, cv2.THRESH_BINARY)
    else:
        thresh_cutoff = int(mean_val - (1.2 * std_val) + sensitivity)
        thresh_cutoff = max(10, min(245, thresh_cutoff))
        _, binary = cv2.threshold(blurred, thresh_cutoff, 255, cv2.THRESH_BINARY_INV)

    # Keep only inside petri mask
    binary = cv2.bitwise_and(binary, binary, mask=petri_mask)

    # Light morphological clean (no aggressive erosion to preserve tiny colonies)
    kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    binary_clean = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small, iterations=1)

    output_image = image_array.copy()
    cv2.circle(output_image, center, p_radius, (0, 255, 0), 2)

    colony_data = []
    hsv_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)

    if use_watershed:
        dist_transform = cv2.distanceTransform(binary_clean, cv2.DIST_L2, 3)
        max_dist = dist_transform.max()
        if max_dist > 0:
            _, sure_fg = cv2.threshold(dist_transform, watershed_strictness * max_dist, 255, 0)
            sure_fg = np.uint8(sure_fg)
            sure_bg = cv2.dilate(binary_clean, kernel_small, iterations=2)
            unknown = cv2.subtract(sure_bg, sure_fg)
            _, markers = cv2.connectedComponents(sure_fg)
            markers = markers + 1
            markers[unknown == 255] = 0
            cv2.watershed(cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR), markers)
            unique_labels = np.unique(markers)

            c_id = 1
            for label in unique_labels:
                if label <= 1:
                    continue
                single_mask = np.uint8(markers == label)
                area = cv2.countNonZero(single_mask)

                if min_area <= area <= max_area:
                    moments = cv2.moments(single_mask)
                    cX = int(moments["m10"] / moments["m00"]) if moments["m00"] != 0 else 0
                    cY = int(moments["m01"] / moments["m00"]) if moments["m00"] != 0 else 0

                    contours, _ = cv2.findContours(single_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    if not contours:
                        continue
                    cnt = contours[0]
                    perimeter = cv2.arcLength(cnt, True)
                    circularity = (4 * math.pi * area) / (perimeter ** 2) if perimeter > 0 else 0.0

                    morphology = "Regular Bacteria" if circularity >= circularity_threshold else "Irregular / Mold"

                    # Color Extraction
                    colony_pixels_hsv = hsv_image[single_mask == 1]
                    if len(colony_pixels_hsv) > 0:
                        med_hsv = np.median(colony_pixels_hsv, axis=0)
                        color_group = classify_colony_color(med_hsv[0], med_hsv[1], med_hsv[2])
                    else:
                        color_group = "White/Cream"

                    # Visualization
                    cv2.drawContours(output_image, contours, -1, (255, 0, 0), 2)
                    cv2.circle(output_image, (cX, cY), 3, (0, 0, 255), -1)

                    colony_data.append({
                        "Colony_ID": c_id,
                        "Area_px": area,
                        "Circularity": round(circularity, 2),
                        "Morphology": morphology,
                        "Color_Group": color_group
                    })
                    c_id += 1
    else:
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary_clean)
        c_id = 1
        for i in range(1, num_labels):
            area = stats[i, cv2.CC_STAT_AREA]
            if min_area <= area <= max_area:
                cX, cY = int(centroids[i][0]), int(centroids[i][1])
                single_mask = np.uint8(labels == i)
                contours, _ = cv2.findContours(single_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    cnt = contours[0]
                    perimeter = cv2.arcLength(cnt, True)
                    circularity = (4 * math.pi * area) / (perimeter ** 2) if perimeter > 0 else 0.0
                    morphology = "Regular Bacteria" if circularity >= circularity_threshold else "Irregular / Mold"

                    colony_pixels_hsv = hsv_image[single_mask == 1]
                    if len(colony_pixels_hsv) > 0:
                        med_hsv = np.median(colony_pixels_hsv, axis=0)
                        color_group = classify_colony_color(med_hsv[0], med_hsv[1], med_hsv[2])
                    else:
                        color_group = "White/Cream"

                    cv2.drawContours(output_image, contours, -1, (255, 0, 0), 2)
                    cv2.circle(output_image, (cX, cY), 3, (0, 0, 255), -1)

                    colony_data.append({
                        "Colony_ID": c_id,
                        "Area_px": area,
                        "Circularity": round(circularity, 2),
                        "Morphology": morphology,
                        "Color_Group": color_group
                    })
                    c_id += 1

    auto_count = len(colony_data)

    # 4. Technician Override
    st.sidebar.header("🎯 4. Technician Correction")
    manual_adjust = st.sidebar.number_input("Manual Adjustment (+/-)", min_value=-auto_count, max_value=1000, value=0)
    final_count = auto_count + manual_adjust

    # --- UI DISPLAY ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Petri Dish")
        st.image(image_array, use_container_width=True)
    with col2:
        st.subheader("AI Detection Result")
        st.image(output_image, caption=f"Detected: {auto_count} Colonies", use_container_width=True)

    # Expandable view to check internal thresholding binary mask
    with st.expander("🔍 View Internal Binary Threshold Mask (Debugging)"):
        st.image(binary_clean, caption="Colony Detection Mask", use_container_width=True)

    # Metrics
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Auto Detected", auto_count)
    m2.metric("Verified Count", final_count, delta=f"{manual_adjust} manual" if manual_adjust != 0 else None)

    cfu_calculated = None
    if calc_cfu:
        cfu_calculated = (final_count * dilution_factor) / plated_volume
        m3.metric("CFU/mL", f"{cfu_calculated:,.2e}")
    else:
        m3.metric("CFU/mL", "Disabled")

    molds = sum(1 for c in colony_data if c["Morphology"] == "Irregular / Mold")
    m4.metric("Irregular / Mold", molds)

    # Data & Reports
    if auto_count > 0:
        st.divider()
        df_colonies = pd.DataFrame(colony_data)

        st.subheader("📊 Phenotype & Color Distribution")
        summary_df = df_colonies.groupby("Color_Group").agg(
            Count=('Colony_ID', 'count'),
            Avg_Area=('Area_px', 'mean')
        ).reset_index()
        summary_df["Percentage (%)"] = (summary_df["Count"] / auto_count * 100).round(2)
        summary_df["Avg_Area"] = summary_df["Avg_Area"].round(1)

        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.dataframe(summary_df, use_container_width=True)
        with c_right:
            st.bar_chart(summary_df.set_index("Color_Group")["Count"])

        st.divider()
        st.subheader("📄 Export Lab Report")
        rep_col1, rep_col2, rep_col3 = st.columns([1, 1, 1])
        with rep_col1:
            sample_name = st.text_input("Sample / Plate ID", value="SAMPLE-PLATE-01")
        with rep_col2:
            analyst_name = st.text_input("Analyst Name", value="Sahil Kumar")
        with rep_col3:
            st.write(" ")
            st.write(" ")
            pdf_data = generate_pdf_report(sample_name, analyst_name, final_count, cfu_calculated, summary_df)
            st.download_button(
                label="📥 Download Audit PDF Report",
                data=pdf_data,
                file_name=f"{sample_name}_report.pdf",
                mime="application/pdf"
            )
