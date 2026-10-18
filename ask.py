
import numpy as np

def calculate_daily_trading_bounds(spot_price, vxn_volatility, levels):
    """
    Calculates daily statistical price boundaries using VXN volatility.
    """
    daily_volatility = (vxn_volatility / 100) / np.sqrt(252)

    results = {
        "Spot Price": round(spot_price, 2)
    }

    confidence_levels = {
        "68": (1.0, "68.27%"),
        "90": (1.645, "90%"),
        "95": (1.96, "95%"),
        "99": (2.576, "99%")
    }

    for level in levels:
        z_score, label = confidence_levels[level]
        move = spot_price * daily_volatility * z_score

        results[f"{label} Upper"] = round(spot_price + move, 2)
        results[f"{label} Lower"] = round(spot_price - move, 2)
        results[f"{label} Expected Move"] = round(move, 2)

    return results


# Ask for inputs
spot_price = float(input("Enter QQQ spot price: $"))
vxn_volatility = float(input("Enter VXN volatility (e.g. 27.13): "))

print("\nAvailable confidence levels: 68, 90, 95, 99")
selected_levels = input(
    "Enter the confidence levels you want, separated by commas (e.g. 68,90,95): "
)

levels = [level.strip() for level in selected_levels.split(",")]

# Validate input
valid_levels = {"68", "90", "95", "99"}

if not levels or any(level not in valid_levels for level in levels):
    print("Invalid selection. Choose from 68, 90, 95, or 99.")
else:
    results = calculate_daily_trading_bounds(
        spot_price, vxn_volatility, levels
    )

    print("\n--- QQQ Statistical Trading Levels ---")
    for level, price in results.items():
        if level == "Spot Price":
            print(f"{level}: ${price:.2f}")
        elif "Expected Move" in level:
            print(f"{level}: +/- ${price:.2f}")
        else:
            print(f"{level}: ${price:.2f}")
