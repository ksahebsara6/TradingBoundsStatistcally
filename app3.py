import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="QQQ Volatility Confidence Intervals",
    page_icon="📈",
    layout="wide",
)

st.title("QQQ Volatility Confidence Intervals")
st.caption(
    "Estimate statistical daily price ranges from annualized VXN implied volatility. "
    "These are model estimates, not guaranteed support/resistance levels."
)

with st.sidebar:
    st.header("Market Inputs")
    spot_price = st.number_input(
        "QQQ spot price ($)", min_value=0.01, value=709.80, step=0.10, format="%.2f"
    )
    vxn_volatility = st.number_input(
        "VXN implied volatility (%)", min_value=0.01, value=27.13, step=0.10, format="%.2f"
    )
    trading_days = st.number_input(
        "Trading days per year", min_value=1, max_value=366, value=252, step=1
    )
    selected_levels = st.multiselect(
        "Confidence intervals",
        options=["68%", "90%", "95%", "99%"],
        default=["68%", "90%", "95%"],
    )

Z_SCORES = {
    "68%": 1.0,
    "90%": 1.6448536269514722,
    "95%": 1.959963984540054,
    "99%": 2.5758293035489004,
}

if not selected_levels:
    st.info("Select at least one confidence interval in the sidebar to display results.")
    st.stop()

daily_volatility = (vxn_volatility / 100) / np.sqrt(trading_days)
one_sigma_move = spot_price * daily_volatility
daily_move_pct = daily_volatility * 100

rows = []
for level in selected_levels:
    z = Z_SCORES[level]
    move = spot_price * daily_volatility * z
    rows.append(
        {
            "Confidence interval": level,
            "Z-score": z,
            "Expected move ($)": move,
            "Expected move (%)": (move / spot_price) * 100,
            "Lower bound ($)": spot_price - move,
            "Upper bound ($)": spot_price + move,
        }
    )

df = pd.DataFrame(rows)

m1, m2, m3 = st.columns(3)
m1.metric("QQQ Spot Price", f"${spot_price:,.2f}")
m2.metric("Daily Implied Volatility (approx.)", f"{daily_move_pct:.2f}%")
m3.metric("1σ Expected Daily Move", f"±${one_sigma_move:,.2f}")

st.subheader("Calculated Price Levels")
display_df = df.copy()
for col in ["Z-score", "Expected move ($)", "Expected move (%)", "Lower bound ($)", "Upper bound ($)"]:
    if col == "Z-score":
        display_df[col] = display_df[col].map(lambda x: f"{x:.3f}")
    elif col == "Expected move (%)":
        display_df[col] = display_df[col].map(lambda x: f"±{x:.2f}%")
    elif col == "Expected move ($)":
        display_df[col] = display_df[col].map(lambda x: f"±${x:,.2f}")
    else:
        display_df[col] = display_df[col].map(lambda x: f"${x:,.2f}")
st.dataframe(display_df, use_container_width=True, hide_index=True)

st.subheader("Price Range Visualization")
fig, ax = plt.subplots(figsize=(10, max(3.2, 0.9 * len(df))))
y_positions = list(range(len(df)))
for y, row in enumerate(rows):
    ax.plot([row["Lower bound ($)"], row["Upper bound ($)"]], [y, y], linewidth=7, solid_capstyle="round")
    ax.scatter([row["Lower bound ($)"], row["Upper bound ($)"]], [y, y], s=45)
ax.axvline(spot_price, linestyle="--", linewidth=1.5, label=f"Spot ${spot_price:,.2f}")
ax.set_yticks(y_positions)
ax.set_yticklabels([row["Confidence interval"] for row in rows])
ax.set_xlabel("QQQ price ($)")
ax.set_ylabel("Confidence interval")
ax.grid(axis="x", alpha=0.25)
ax.legend()
fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)

csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download levels as CSV",
    data=csv,
    file_name="qqq_volatility_confidence_intervals.csv",
    mime="text/csv",
)

with st.expander("Method and assumptions"):
    st.markdown(
        r"""
        - Daily volatility estimate: annualized VXN volatility ÷ √(trading days per year).
        - Expected move at a selected interval: spot price × daily volatility × z-score.
        - Bounds are calculated as spot price ± expected move.
        - The 90% interval uses a two-sided normal z-score of approximately 1.645.
        - This is a simplified normal-return estimate. VXN is a Nasdaq-100 volatility index, so applying it directly to QQQ is an approximation. Realized moves can fall outside these ranges.
        """
    )
