import streamlit as st

# ---------- Cấu hình trang ----------
st.set_page_config(page_title="Tính Chỉ Số BMI", page_icon="⚖️", layout="centered")

# ---------- Màu sắc theo từng nhóm phân loại ----------
COLORS = {
    "thieu": "#5B8DBE",       # Thiếu cân
    "binhthuong": "#3E8E5B",  # Bình thường
    "thua": "#C98A2E",        # Thừa cân
    "beophi": "#B4483C",      # Béo phì
}

SCALE_MIN = 15
SCALE_MAX = 40


def classify(bmi: float):
    if bmi < 18.5:
        return "Thiếu cân", COLORS["thieu"]
    if bmi < 25:
        return "Bình thường", COLORS["binhthuong"]
    if bmi < 30:
        return "Thừa cân", COLORS["thua"]
    return "Béo phì", COLORS["beophi"]


def render_result(weight: float, height: float) -> str:
    h_m = height / 100
    bmi = weight / (h_m * h_m)
    bmi_rounded = round(bmi, 1)
    label, color = classify(bmi)

    clamped = min(max(bmi, SCALE_MIN), SCALE_MAX)
    pct = (clamped - SCALE_MIN) / (SCALE_MAX - SCALE_MIN) * 100

    html = f"""
    <div style="text-align:center; font-family:'Inter',sans-serif;">
      <div style="font-family:'Fraunces',serif; font-size:64px; font-weight:600;
                  line-height:1; letter-spacing:-0.02em; color:{color};">
        {bmi_rounded:.1f}
      </div>
      <div style="font-family:'IBM Plex Mono',monospace; font-size:13px;
                  color:#5B6E68; margin-top:2px; letter-spacing:0.05em;">
        kg/m&sup2;
      </div>
      <div style="display:inline-block; margin-top:14px; padding:6px 16px;
                  border-radius:999px; font-size:13.5px; font-weight:700;
                  color:#fff; background:{color};">
        {label}
      </div>

      <div style="margin-top:26px;">
        <div style="display:flex; height:10px; border-radius:6px; overflow:hidden;
                    position:relative;">
          <span style="width:14%; background:{COLORS['thieu']};"></span>
          <span style="width:26%; background:{COLORS['binhthuong']};"></span>
          <span style="width:20%; background:{COLORS['thua']};"></span>
          <span style="width:40%; background:{COLORS['beophi']};"></span>
          <div style="position:absolute; top:-6px; left:calc({pct}% - 1px);
                      width:2px; height:22px; background:#1B3A34; border-radius:2px;">
          </div>
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:10px;
                    font-size:10.5px; color:#5B6E68; font-family:'IBM Plex Mono',monospace;">
          <div>Thiếu cân</div>
          <div>Bình thường</div>
          <div>Thừa cân</div>
          <div>Béo phì</div>
        </div>
      </div>
    </div>
    """
    return html


CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600&family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@500;600&display=swap');

.stApp {
    background: #EEF3EC;
    font-family: 'Inter', sans-serif;
}
#bmi-title {
    font-family: 'Fraunces', serif;
    font-weight: 600;
    letter-spacing: -0.01em;
    color: #1B3A34;
    margin-bottom: 2px;
}
#bmi-desc {
    color: #5B6E68;
    font-size: 14.5px;
    margin-bottom: 24px;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: #FFFFFF;
    border: 1px solid #DCE6DF;
    border-radius: 20px;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("<h1 id='bmi-title'>Tính chỉ số BMI</h1>", unsafe_allow_html=True)
    st.markdown(
        "<p id='bmi-desc'>Kéo thanh trượt để nhập cân nặng và chiều cao, "
        "chỉ số khối cơ thể (BMI) sẽ được tính ngay lập tức.</p>",
        unsafe_allow_html=True,
    )

    weight = st.slider("Cân nặng (kg)", min_value=30, max_value=200, value=60, step=1)
    height = st.slider("Chiều cao (cm)", min_value=100, max_value=220, value=165, step=1)

    st.markdown(render_result(weight, height), unsafe_allow_html=True)
