import streamlit as st
import cv2
import numpy as np
from PIL import Image
import pandas as pd
import io

st.set_page_config(
    page_title="Colony Counter Pro",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Automated Bacterial Colony Counter Pro")
st.caption("Computer Vision & Watershed Segmentation for Petri Dish Colony Counting")

# --- SIDEBAR CONTROLS ---
st.sidebar.header("⚙️ Detection Parameters")

invert_image = st.sidebar.checkbox("Invert Image (Check if colonies are darker than agar)", value=False)
blur_ksize = st.sidebar.slider("Noise Reduction (Gaussian Blur)", min_value=3, max_value=21, value=9, step=2)

use_watershed = st.sidebar.checkbox("Enable Watershed (Split touching colonies)", value=True)
watershed_threshold = st.sidebar.slider("Separation Strictness (Watershed)", min_value=0.1, max_value=0.9, value=0.4, step=0.05)

st.sidebar.subheader("Filter by Colony Size (Pixels)")
min_area = st.sidebar.number_input("Min Colony Area (px²)", min_value=1, max_value=5000, value=15)
max_area = st.sidebar.number_input("Max Colony Area (px²)", min_value=50, max_value=50000, value=5000)

st.sidebar.subheader("🧫 Microbiology CFU Calculator")
calc_cfu = st.sidebar.checkbox("Calculate CFU/mL", value=False)
if calc_cfu:
    dilution_factor = st.sidebar.number_input("Dilution Factor (e.g., 1000 for 10^-3)", min_value=1.0, value=100.0)
    plated_volume = st.sidebar.number_input("Volume Plated (in mL, e.g. 0.1)", min_value=0.001, max_value=10.0, value=0.1, step=0.01)

# --- FILE UPLOADER ---
uploaded_file = st.file_uploader("Upload Petri Dish Image", type=["jpg", "jpeg", "png"])

def apply_circular_mask(img_gray):
    """Petri dish ke rim aur background noise ko exclude karne ke liye circular mask"""
    h, w = img_gray.shape
    center = (int(w / 2), int(h / 2))
    radius = int(min(h, w) * 0.46)  # 46% covering to stay inside rim
    mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(mask, center, radius, 255, -1)
    masked_img = cv2.bitwise_and(img_gray, img_gray, mask=mask)
    return masked_img, mask, center, radius

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    image_array = np.array(image)
    h, w, _ = image_array.shape

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Image")
        st.image(image, caption="Uploaded Petri Dish", width="stretch")

    # Grayscale aur Blur
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)

    # Circular ROI Mask
    masked_gray, petri_mask, center, p_radius = apply_circular_mask(blurred)

    # Thresholding
    thresh_flag = cv2.THRESH_BINARY if invert_image else cv2.THRESH_BINARY_INV
    _, thresh = cv2.threshold(masked_gray, 0, 255, thresh_flag + cv2.THRESH_OTSU)
    thresh = cv2.bitwise_and(thresh, thresh, mask=petri_mask)

    output_image = image_array.copy()
    # Draw petri dish border guide
    cv2.circle(output_image, center, p_radius, (255, 165, 0), 2)

    colony_data = []

    if use_watershed:
        # Morphological opening to remove tiny noise
        kernel = np.ones((3, 3), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)

        # Sure background
        sure_bg = cv2.dilate(opening, kernel, iterations=3)

        # Distance transform to separate merged colonies
        dist_transform = cv2.distanceTransform(opening, cv2.DIST_L2, 5)
        _, sure_fg = cv2.threshold(dist_transform, watershed_threshold * dist_transform.max(), 255, 0)
        sure_fg = np.uint8(sure_fg)

        # Unknown boundary region
        unknown = cv2.subtract(sure_bg, sure_fg)

        # Marker labeling
        _, markers = cv2.connectedComponents(sure_fg)
        markers = markers + 1
        markers[unknown == 255] = 0

        # Watershed segmentation
        markers = cv2.watershed(cv2.cvtColor(masked_gray, cv2.COLOR_GRAY2BGR), markers)
        
        unique_markers = np.unique(markers)
        colony_id = 1
        for marker in unique_markers:
            if marker <= 1:
                continue
            marker_mask = np.uint8(markers == marker)
            contours, _ = cv2.findContours(marker_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for c in contours:
                area = cv2.contourArea(c)
                if min_area <= area <= max_area:
                    ((x, y), radius) = cv2.minEnclosingCircle(c)
                    cv2.circle(output_image, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                    colony_data.append({"Colony_ID": colony_id, "X": int(x), "Y": int(y), "Area_px": int(area), "Radius_px": round(radius, 2)})
                    colony_id += 1
    else:
        # Standard contour detection
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        colony_id = 1
        for c in contours:
            area = cv2.contourArea(c)
            if min_area <= area <= max_area:
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                cv2.circle(output_image, (int(x), int(y)), int(radius), (0, 255, 0), 2)
                colony_data.append({"Colony_ID": colony_id, "X": int(x), "Y": int(y), "Area_px": int(area), "Radius_px": round(radius, 2)})
                colony_id += 1

    total_count = len(colony_data)

    with col2:
        st.subheader("Analyzed Colonies")
        st.image(output_image, caption=f"Identified {total_count} colonies (Orange line: Dish boundary)", width="stretch")

    # --- RESULTS SUMMARY ---
    st.divider()
    metric_cols = st.columns(3 if calc_cfu else 2)
    metric_cols[0].metric(label="Total Colony Count", value=f"{total_count} CFU")
    
    avg_area = round(np.mean([d["Area_px"] for d in colony_data]), 2) if colony_data else 0
    metric_cols[1].metric(label="Average Colony Area", value=f"{avg_area} px²")

    if calc_cfu:
        cfu_ml = (total_count * dilution_factor) / plated_volume if plated_volume > 0 else 0
        metric_cols[2].metric(label="Calculated CFU/mL", value=f"{cfu_ml:.2e}")

    # --- DATA EXPORT ---
    if total_count > 0:
        df = pd.DataFrame(colony_data)
        with st.expander("📊 View Detailed Colony Coordinates & Sizes"):
            st.dataframe(df, width="stretch")

        csv_buffer = io.StringIO()
        df.to_csv(csv_buffer, index=False)
        st.download_button(
            label="📥 Download Results as CSV",
            data=csv_buffer.getvalue(),
            file_name="colony_count_results.csv",
            mime="text/csv"
        )
        
