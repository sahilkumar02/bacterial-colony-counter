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
    page_title="AI Colony Counter & Lab Phenotyping Suite",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 AI-Powered Colony Counter & Strain Phenotyping Suite")
st.caption("Computer Vision • Glare Inpainting • Morphology/Contamination Analysis • Color Phenotyping • Audit Reports")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ 1. Preprocessing & Glare Control")
remove_glare = st.sidebar.checkbox("Auto-Remove Glare / Lid Reflections", value=True)
glare_thresh = st.sidebar.slider("Glare Sensitivity", 180, 255, 235)
blur_ksize = st.sidebar.slider("Noise Reduction (Gaussian Blur)", 3, 21, 9, step=2)
invert_image = st.sidebar.checkbox("Invert Agar Contrast (Dark Colonies on Light Agar)", value=False)

st.sidebar.header("🧫 2. Segmentation & Filtering")
use_watershed = st.sidebar.checkbox("Enable Watershed (Split Clustered Colonies)", value=True)
watershed_threshold = st.sidebar.slider("Separation Strictness", 0.1, 0.9, 0.45, 0.05)
min_area = st.sidebar.number_input("Min Colony Area (px²)", min_value=1, max_value=5000, value=20)
max_area = st.sidebar.number_input("Max Colony Area (px²)", min_value=50, max_value=50000, value=6000)

st.sidebar.header("🎨 3. Phenotype & Contamination")
enable_color = st.sidebar.checkbox("Enable Color Classification", value=True)
circularity_threshold = st.sidebar.slider("Morphology Cutoff (Circularity Index)", 0.3, 0.9, 0.65, 0.05,
                                         help="Colonies with score below this are classified as Irregular / Fungal Contamination")

st.sidebar.header("🔢 4. CFU Calculator")
calc_cfu = st.sidebar.checkbox("Calculate CFU/mL", value=False)
if calc_cfu:
    dilution_factor = st.sidebar.number_input("Dilution Factor (e.g. 1000 for 10^-3)", min_value=1.0, value=100.0)
    plated_volume = st.sidebar.number_input("Volume Plated (in mL, e.g. 0.1)", min_value=0.001, max_value=10.0, value=0.1)

# Helper: Glare Removal via Inpainting
def clean_glare(img_rgb, thresh_val):
    gray = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2GRAY)
    _, glare_mask = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
    # Dilate slightly to cover edges of glare spots
    kernel = np.ones((5, 5), np.uint8)
    glare_mask = cv2.dilate(glare_mask, kernel, iterations=1)
    # Fast Marching Inpainting
    cleaned = cv2.inpaint(img_rgb, glare_mask, 5, cv2.INPAINT_TELEA)
    return cleaned

# Helper: Color Classification
def classify_colony_color(h, s, v):
    if v < 45:
        return "Black/Dark"
    if s < 35:
        return "White/Cream" if v > 175 else "Translucent/Gray"
    
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
def apply_circular_mask(img_gray):
    h, w = img_gray.shape
    center = (int(w / 2), int(h / 2))
    radius = int(min(h, w) * 0.46)
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, center, radius, 255, -1)
    masked_img = cv2.bitwise_and(img_gray, img_gray, mask=mask)
    return masked_img, mask, center, radius

# Helper: PDF Generation
def generate_pdf_report(sample_id, analyst_name, total_count, cfu_val, df_summary):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()
    story = []

    # Title & Metadata
    title_style = ParagraphStyle(name='TitleStyle', parent=styles['Heading1'], fontSize=18, textColor=colors.HexColor('#0f52ba'))
    story.append(Paragraph("Microbiology Laboratory Analysis Report", title_style))
    story.append(Paragraph(f"<b>Generated On:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | <b>Analyst:</b> {analyst_name}", styles['Normal']))
    story.append(Paragraph(f"<b>Sample / Plate ID:</b> {sample_id}", styles['Normal']))
    story.append(Spacer(1, 15))

    # Summary Metrics
    cfu_str = f"{cfu_val:,.2e} CFU/mL" if cfu_val is not None else "Not Calculated"
    summary_data = [
        ["Total Colony Count", "Morphology Status", "CFU Calculation"],
        [str(total_count), "Automated Segmentation Completed", cfu_str]
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

    # Color/Phenotype Breakdown
    story.append(Paragraph("<b>Strain Phenotype & Colony Breakdown:</b>", styles['Heading3']))
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

# --- MAIN WORKFLOW ---
uploaded_file = st.file_uploader("Upload Petri Dish Image", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    raw_image = Image.open(uploaded_file).convert("RGB")
    image_array = np.array(raw_image)

    # Glare removal step
    if remove_glare:
        image_array = clean_glare(image_array, glare_thresh)

    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    masked_gray, petri_mask, center, p_radius = apply_circular_mask(blurred)

    thresh_flag = cv2.THRESH_BINARY if invert_image else cv2.THRESH_BINARY_INV
    _, thresh = cv2.threshold(masked_gray, 0, 255, thresh_flag + cv2.THRESH_OTSU)
    thresh = cv2.bitwise_and(thresh, thresh, mask=petri_mask)

    output_image = image_array.copy()
    cv2.circle(output_image, center, p_radius, (0, 255, 0), 2)

    colony_data = []
    hsv_image = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)

    if use_watershed:
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, watershed_threshold * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)

        unknown = cv2.subtract(sure_bg, sure_fg)
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        markers = cv2.watershed(cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR), markers)
        unique_labels = np.unique(markers)

        colony_id = 1
        for label in unique_labels:
            if label <= 1:
                continue

            single_colony_mask = np.uint8(markers == label)
            area = cv2.countNonZero(single_colony_mask)

            if min_area <= area <= max_area:
                moments = cv2.moments(single_colony_mask)
                cX = int(moments["m10"] / moments["m00"]) if moments["m00"] != 0 else 0
                cY = int(moments["m01"] / moments["m00"]) if moments["m00"] != 0 else 0

                contours, _ = cv2.findContours(single_colony_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if not contours:
                    continue
                cnt = contours[0]
                perimeter = cv2.arcLength(cnt, True)
                circularity = (4 * math.pi * area) / (perimeter ** 2) if perimeter > 0 else 0.0

                morphology_type = "Regular Bacteria" if circularity >= circularity_threshold else "Irregular / Mold"

                # Color phenotyping
                colony_pixels_hsv = hsv_image[single_colony_mask == 1]
                med_hsv = np.median(colony_pixels_hsv, axis=0)
                color_name = classify_colony_color(med_hsv[0], med_hsv[1], med_hsv[2])

                # Overlay marking: Red contour for bacteria, Yellow for mold/irregular
                border_color = (255, 0, 0) if morphology_type == "Regular Bacteria" else (255, 215, 0)
                cv2.drawContours(output_image, contours, -1, border_color, 2)
                cv2.circle(output_image, (cX, cY), 2, (0, 0, 255), -1)

                colony_data.append({
                    "Colony_ID": colony_id,
                    "Centroid_X": cX,
                    "Centroid_Y": cY,
                    "Area_px": area,
                    "Circularity": round(circularity, 2),
                    "Morphology": morphology_type,
                    "Color_Group": color_name
                })
                colony_id += 1

    auto_detected_count = len(colony_data)

    # --- HUMAN-IN-THE-LOOP ZERO-ERROR ADJUSTMENT ---
    st.sidebar.header("🎯 5. Zero-Error Manual Override")
    manual_adjust = st.sidebar.number_input(
        "Technician Correction (+/- colonies)",
        min_value=-auto_detected_count,
        max_value=1000,
        value=0,
        help="Use this to add missed colonies or remove false positives."
    )
    final_verified_count = auto_detected_count + manual_adjust

    # --- DISPLAY ORIGINAL VS SEGMENTED ---
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Plate (Glare Cleaned)")
        st.image(image_array, caption="Preprocessed Image", use_container_width=True)
    with col2:
        st.subheader("AI Segmentation & Phenotyping")
        st.image(output_image, caption=f"Detected: {auto_detected_count} | Verified: {final_verified_count}", use_container_width=True)

    # --- METRICS BAR ---
    st.divider()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Auto Detected", auto_detected_count)
    m2.metric("Final Verified Count", final_verified_count, delta=f"{manual_adjust} manual" if manual_adjust != 0 else None)

    cfu_calculated = None
    if calc_cfu:
        cfu_calculated = (final_verified_count * dilution_factor) / plated_volume
        m3.metric("CFU/mL", f"{cfu_calculated:,.2e}")
    else:
        m3.metric("CFU/mL", "Disabled")

    mold_count = sum(1 for c in colony_data if c["Morphology"] == "Irregular / Mold")
    m4.metric("Contamination / Mold", mold_count)

    # --- TABLES & EXPORTS ---
    if auto_detected_count > 0:
        st.divider()
        df_colonies = pd.DataFrame(colony_data)

        st.subheader("📊 Colony Phenotype & Strain Breakdown")
        summary_df = df_colonies.groupby("Color_Group").agg(
            Count=('Colony_ID', 'count'),
            Avg_Area=('Area_px', 'mean')
        ).reset_index()
        summary_df["Percentage (%)"] = (summary_df["Count"] / auto_detected_count * 100).round(2)
        summary_df["Avg_Area"] = summary_df["Avg_Area"].round(1)

        c_left, c_right = st.columns([1, 1])
        with c_left:
            st.dataframe(summary_df, use_container_width=True)
        with c_right:
            st.bar_chart(summary_df.set_index("Color_Group")["Count"])

        # --- AUDIT EXPORT SECTION ---
        st.divider()
        st.subheader("📄 Export Lab Documentation")
        rep_col1, rep_col2, rep_col3 = st.columns([1, 1, 1])

        with rep_col1:
            sample_name = st.text_input("Sample / Plate ID", value="SAMPLE-PLATE-01")
        with rep_col2:
            analyst_name = st.text_input("Analyst / Lab Tech", value="Sahil Kumar")

        with rep_col3:
            st.write(" ")
            st.write(" ")
            # Generate PDF
            pdf_data = generate_pdf_report(
                sample_name,
                analyst_name,
                final_verified_count,
                cfu_calculated,
                summary_df
            )
            st.download_button(
                label="📥 Download Audit PDF Report",
                data=pdf_data,
                file_name=f"{sample_name}_Colony_Report.pdf",
                mime="application/pdf"
            )

        # CSV Download
        csv_buffer = io.StringIO()
        df_colonies.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Raw Colony Coordinates (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"{sample_name}_raw_data.csv",
            mime="text/csv"
        )
