import streamlit as st
import cv2
import numpy as np
from PIL import Image

st.set_page_config(
    page_title="Colony Counter App",
    page_icon="🔬",
    layout="wide"
)

st.title("🔬 Automated Bacterial Colony Counter")
st.write("Upload a Petri dish image to begin colony analysis.")

uploaded_file = st.file_uploader(
    "Upload Petri Dish Image",
    type=["jpg", "jpeg", "png"]
)

if uploaded_file is not None:
    image = Image.open(uploaded_file).convert("RGB")
    image_array = np.array(image)

    st.image(image, caption="Uploaded Petri Dish", use_container_width=True)
    st.success("Image uploaded successfully!")

    # OpenCV processing aur counting
    gray = cv2.cvtColor(image_array, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (11, 11), 0)
    _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    colony_count = 0
    output_image = image_array.copy()
    for c in contours:
        if cv2.contourArea(c) > 5:
            colony_count += 1
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            cv2.circle(output_image, (int(x), int(y)), int(radius), (0, 255, 0), 2)

    st.write(f"### Total Colonies Detected: {colony_count}")
    st.image(output_image, caption="Analyzed Colonies", use_container_width=True)
  
