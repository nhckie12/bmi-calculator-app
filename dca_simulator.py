import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ==========================================================
# Cấu hình trang
# ==========================================================
st.set_page_config(page_title="Mô phỏng đầu tư định kỳ", page_icon="📈", layout="wide")

st.title("📈 Mô phỏng đầu tư định kỳ hàng tháng (DCA)")
st.caption(
    "Ước tính giá trị tài sản khi đầu tư đều đặn mỗi tháng, có tính đến biến động "
    "thị trường và các cú sốc bất thường (tăng/giảm mạnh đột ngột)."
)

# ==========================================================
# Bảng điều khiển đầu vào
# ==========================================================
with st.sidebar:
    st.header("Thông số đầu vào")

    monthly_amount = st.number_input(
        "Số tiền đầu tư mỗi tháng (triệu đồng)",
        min_value=0.5, max_value=500.0, value=10.0, step=0.5,
    )

    years = st.slider("Kỳ hạn đầu tư (năm)", min_value=1, max_value=30, value=10)
    n_months = years * 12

    st.subheader("Mô hình lợi nhuận")
    annual_return = st.slider(
        "Lợi nhuận kỳ vọng bình quân / năm (%)",
        min_value=-10.0, max_value=30.0, value=10.0, step=0.5,
    )
    annual_vol = st.slider(
        "Độ biến động (volatility) / năm (%)",
        min_value=1.0, max_value=60.0, value=15.0, step=1.0,
    )

    st.subheader("Biến động bất thường (jump/shock)")
    enable_shock = st.checkbox("Bật mô phỏng cú sốc bất thường", value=True)

    if enable_shock:
        shock_prob = st.slider(
            "Xác suất xảy ra cú sốc mỗi tháng (%)",
            min_value=0.0, max_value=20.0, value=4.0, step=0.5,
        )
        shock_mean = st.slider(
            "Biên độ trung bình của cú sốc (%)",
            min_value=-60.0, max_value=60.0, value=-18.0, step=1.0,
            help="Âm = thiên về sụt giảm mạnh (khủng hoảng), dương = thiên về tăng vọt.",
        )
        shock_std = st.slider(
            "Độ phân tán của cú sốc (%)", min_value=1.0, max_value=40.0, value=12.0, step=1.0,
        )
    else:
        shock_prob, shock_mean, shock_std = 0.0, 0.0, 0.0

    st.subheader("Mô phỏng Monte Carlo")
    n_sims = st.slider("Số kịch bản mô phỏng", min_value=100, max_value=3000, value=800, step=100)
    seed = st.number_input("Seed ngẫu nhiên (tuỳ chọn, để tái lập kết quả)", min_value=0, value=42, step=1)

    run_btn = st.button("▶ Chạy mô phỏng", type="primary", use_container_width=True)

# ==========================================================
# Mô hình: DCA + Geometric Brownian Motion + Jump Diffusion
# ==========================================================
def simulate(n_months, monthly_amount, annual_return, annual_vol,
             shock_prob, shock_mean, shock_std, n_sims, seed):
    rng = np.random.default_rng(seed)

    mu_m = (1 + annual_return / 100) ** (1 / 12) - 1     # lợi nhuận kỳ vọng / tháng
    sigma_m = (annual_vol / 100) / np.sqrt(12)            # độ lệch chuẩn / tháng

    # Lợi nhuận thường xuyên (khuếch tán liên tục - phân phối chuẩn)
    normal_returns = rng.normal(mu_m, sigma_m, size=(n_sims, n_months))

    # Cú sốc bất thường (bước nhảy - jump diffusion)
    jump_mask = rng.random((n_sims, n_months)) < (shock_prob / 100)
    jump_size = rng.normal(shock_mean / 100, shock_std / 100, size=(n_sims, n_months))
    jumps = jump_mask * jump_size

    monthly_returns = normal_returns + jumps

    portfolio = np.zeros((n_sims, n_months + 1))
    invested = np.zeros(n_months + 1)

    for t in range(1, n_months + 1):
        portfolio[:, t] = portfolio[:, t - 1] * (1 + monthly_returns[:, t - 1]) + monthly_amount
        invested[t] = invested[t - 1] + monthly_amount

    return portfolio, invested, jump_mask.sum(axis=1)


# ==========================================================
# Chạy & hiển thị kết quả
# ==========================================================
if run_btn:
    with st.spinner("Đang chạy mô phỏng..."):
        portfolio, invested, n_shocks_per_path = simulate(
            n_months, monthly_amount, annual_return, annual_vol,
            shock_prob, shock_mean, shock_std, n_sims, seed,
        )

    months_axis = np.arange(n_months + 1)
    p5 = np.percentile(portfolio, 5, axis=0)
    p25 = np.percentile(portfolio, 25, axis=0)
    p50 = np.percentile(portfolio, 50, axis=0)
    p75 = np.percentile(portfolio, 75, axis=0)
    p95 = np.percentile(portfolio, 95, axis=0)

    final_values = portfolio[:, -1]
    total_invested = invested[-1]
    median_final = np.median(final_values)
    prob_loss = np.mean(final_values < total_invested) * 100

    # ---------- Chỉ số tóm tắt ----------
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tổng vốn đã góp", f"{total_invested:,.0f} triệu")
    c2.metric("Giá trị trung vị cuối kỳ", f"{median_final:,.0f} triệu",
              f"{(median_final - total_invested):,.0f} triệu")
    c3.metric("Lợi nhuận trung vị", f"{(median_final / total_invested - 1) * 100:,.1f} %")
    c4.metric("Xác suất lỗ vốn khi kết thúc", f"{prob_loss:,.1f} %")

    # ---------- Biểu đồ diễn biến giá trị danh mục ----------
    st.subheader("Diễn biến giá trị danh mục theo thời gian")

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=np.concatenate([months_axis, months_axis[::-1]]),
        y=np.concatenate([p95, p5[::-1]]),
        fill="toself", fillcolor="rgba(47,111,98,0.12)",
        line=dict(color="rgba(0,0,0,0)"), name="Khoảng 5% - 95%",
        showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=np.concatenate([months_axis, months_axis[::-1]]),
        y=np.concatenate([p75, p25[::-1]]),
        fill="toself", fillcolor="rgba(47,111,98,0.25)",
        line=dict(color="rgba(0,0,0,0)"), name="Khoảng 25% - 75%",
        showlegend=True,
    ))
    fig.add_trace(go.Scatter(
        x=months_axis, y=p50, line=dict(color="#2F6F62", width=3),
        name="Giá trị trung vị (kịch bản giữa)",
    ))
    fig.add_trace(go.Scatter(
        x=months_axis, y=invested, line=dict(color="#B4483C", width=2, dash="dash"),
        name="Tổng vốn đã góp",
    ))

    fig.update_layout(
        xaxis_title="Tháng",
        yaxis_title="Giá trị (triệu đồng)",
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ---------- Phân phối giá trị cuối kỳ ----------
    st.subheader("Phân phối giá trị danh mục khi kết thúc kỳ đầu tư")

    hist = go.Figure()
    hist.add_trace(go.Histogram(
        x=final_values, nbinsx=60, marker_color="#2F6F62", opacity=0.85,
        name="Số kịch bản",
    ))
    hist.add_vline(x=total_invested, line_dash="dash", line_color="#B4483C",
                    annotation_text="Vốn đã góp", annotation_position="top")
    hist.add_vline(x=median_final, line_dash="solid", line_color="#1B3A34",
                    annotation_text="Trung vị", annotation_position="top")
    hist.update_layout(
        xaxis_title="Giá trị cuối kỳ (triệu đồng)",
        yaxis_title="Số kịch bản mô phỏng",
        margin=dict(t=10, b=10),
        showlegend=False,
    )
    st.plotly_chart(hist, use_container_width=True)

    # ---------- Bảng phân vị chi tiết ----------
    with st.expander("Xem bảng phân vị theo mốc thời gian (mỗi 12 tháng)"):
        idx = list(range(0, n_months + 1, 12))
        if idx[-1] != n_months:
            idx.append(n_months)
        table = pd.DataFrame({
            "Tháng": months_axis[idx],
            "Vốn đã góp": invested[idx],
            "P5": p5[idx],
            "P25": p25[idx],
            "Trung vị (P50)": p50[idx],
            "P75": p75[idx],
            "P95": p95[idx],
        }).round(1)
        st.dataframe(table, use_container_width=True, hide_index=True)

    if enable_shock:
        st.caption(
            f"Trung bình mỗi kịch bản trải qua khoảng "
            f"{n_shocks_per_path.mean():.1f} cú sốc bất thường trong {n_months} tháng."
        )

    st.info(
        "⚠️ Đây là mô hình mô phỏng dựa trên giả định thống kê (lợi nhuận ngẫu nhiên "
        "theo phân phối chuẩn kết hợp các cú sốc bất thường), không phải khuyến nghị đầu tư. "
        "Kết quả thực tế có thể khác biệt đáng kể so với mô phỏng. Vui lòng cân nhắc "
        "kỹ và/hoặc tham khảo ý kiến chuyên gia tài chính trước khi ra quyết định đầu tư.",
        icon="ℹ️",
    )

else:
    st.info("Điều chỉnh thông số ở thanh bên trái rồi nhấn **Chạy mô phỏng** để bắt đầu.")
