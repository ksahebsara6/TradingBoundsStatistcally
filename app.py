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
    forecast_days = st.number_input(
        "Forecast horizon (trading days)", min_value=1, max_value=252, value=1, step=1
    )
    selected_levels = st.multiselect(
        "Confidence intervals",
        options=["50%", "68%", "90%", "95%", "99%"],
        default=["50%", "68%", "90%", "95%"],
    )
    st.subheader("Gamma Levels")
    gamma_levels_text = st.text_area(
        "Enter gamma price levels ($)",
        value="",
        placeholder="Example: 700, 705.5, 710, 715, 720",
        help="Enter price levels separated by commas, spaces, or new lines. These are user-supplied levels; the app does not fetch gamma data automatically.",
    )

Z_SCORES = {
    "50%": 0.6744897501960817,
    "68%": 1.0,
    "90%": 1.6448536269514722,
    "95%": 1.959963984540054,
    "99%": 2.5758293035489004,
}

if not selected_levels:
    st.info("Select at least one confidence interval in the sidebar to display results.")
    st.stop()

# Parse user-entered gamma price levels.
gamma_levels = []
invalid_gamma_entries = []
for token in gamma_levels_text.replace("\n", ",").replace(";", ",").replace(" ", ",").split(","):
    token = token.strip()
    if not token:
        continue
    try:
        level = float(token.replace("$", ""))
        if level <= 0 or not np.isfinite(level):
            raise ValueError
        gamma_levels.append(level)
    except ValueError:
        invalid_gamma_entries.append(token)
gamma_levels = sorted(set(gamma_levels))
if invalid_gamma_entries:
    st.sidebar.warning("Ignored invalid gamma level(s): " + ", ".join(invalid_gamma_entries))

# Expected move = S × (σ / 100) × sqrt(t / 252) × z
# VXN is annualized volatility; forecast_days is the horizon in trading days.
period_volatility = (vxn_volatility / 100) * np.sqrt(forecast_days / trading_days)
one_sigma_move = spot_price * period_volatility
daily_move_pct = period_volatility * 100

rows = []
for level in selected_levels:
    z = Z_SCORES[level]
    move = spot_price * period_volatility * z
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
m2.metric(f"Implied Volatility ({forecast_days} trading day{'s' if forecast_days != 1 else ''}, approx.)", f"{daily_move_pct:.2f}%")
m3.metric(f"1σ Expected Move ({forecast_days} day{'s' if forecast_days != 1 else ''})", f"±${one_sigma_move:,.2f}")

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
for i, gamma_level in enumerate(gamma_levels):
    ax.axvline(
        gamma_level,
        linestyle=":",
        linewidth=1.4,
        alpha=0.85,
        label=f"Gamma ${gamma_level:,.2f}" if i < 8 else None,
    )
if len(gamma_levels) > 8:
    ax.text(0.99, 0.02, f"{len(gamma_levels) - 8} additional gamma levels not labeled", transform=ax.transAxes, ha="right", fontsize=8)
ax.set_yticks(y_positions)
ax.set_yticklabels([row["Confidence interval"] for row in rows])
ax.set_xlabel("QQQ price ($)")
ax.set_ylabel("Confidence interval")
ax.grid(axis="x", alpha=0.25)
ax.legend()
fig.tight_layout()
st.pyplot(fig, use_container_width=True)
plt.close(fig)

if gamma_levels:
    st.subheader("User-Entered Gamma Levels")
    gamma_df = pd.DataFrame({"Gamma level ($)": gamma_levels})
    gamma_df["Distance from spot ($)"] = gamma_df["Gamma level ($)"].map(lambda x: x - spot_price)
    gamma_df["Inside selected confidence range"] = gamma_df["Gamma level ($)"].map(
        lambda x: any(row["Lower bound ($)"] <= x <= row["Upper bound ($)"] for row in rows)
    )
    st.dataframe(
        gamma_df.style.format({"Gamma level ($)": "${:,.2f}", "Distance from spot ($)": "{:+,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )
    st.caption("Gamma levels are plotted as dotted vertical lines. A level inside the statistical range is not automatically support or resistance; interpret it with current options positioning and price action.")

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
        - Expected move: S × (σ / 100) × √(t / 252) × z, where S is QQQ spot, σ is annualized VXN volatility in percent, t is the forecast horizon in trading days, and z is the selected confidence-level Z-score.
        - The app uses the selected trading-days-per-year input as the denominator (normally 252).
        - Bounds are calculated as spot price ± expected move.
        - The 90% interval uses a two-sided normal z-score of approximately 1.645.
        - This is a simplified normal-return estimate. VXN is a Nasdaq-100 volatility index, so applying it directly to QQQ is an approximation. Realized moves can fall outside these ranges.
        """
    )
