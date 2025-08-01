import streamlit as st

def mobile_friendly_view():
    """
    Apply mobile-responsive CSS adjustments.
    Should be used early in app.py layout.
    """
    st.markdown("""
        <style>
            @media (max-width: 768px) {
                .element-container {
                    padding-left: 5px !important;
                    padding-right: 5px !important;
                }
                .stButton>button {
                    width: 100% !important;
                }
            }
        </style>
    """, unsafe_allow_html=True)

def cross_platform_info():
    """
    Display a simple guide or info box for platform support.
    """
    st.info("""
    ✅ **Cross-Platform Compatible**  
    This app is accessible on:
    - 💻 Web browsers (Chrome, Firefox, Edge, Safari)
    - 📱 Mobile browsers (Android/iOS)
    - 🖥️ Desktops (Windows/macOS/Linux)
    - 📷 Works with device cameras or webcam for QR scan.
    """)
