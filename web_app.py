import streamlit as st

st.set_page_config(
    page_title="Photocopy Task Scheduler",
    layout="wide"
)

st.title("Demo web - Photocopy Task Scheduler")

st.write("Ứng dụng đã chạy được trên web.")

if st.button("Chạy mô phỏng thử"):
    st.success("Mô phỏng demo thành công!")