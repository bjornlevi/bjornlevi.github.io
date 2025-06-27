import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from dateutil.relativedelta import relativedelta
from sklearn.linear_model import LinearRegression
import numpy as np

def fetch_cpi_data():
    url = "https://px.hagstofa.is:443/pxis/api/v1/is/Efnahagur/visitolur/1_vnv/1_vnv/VIS01000.px"
    payload = {
        "query": [
            {"code": "Vísitala", "selection": {"filter": "item", "values": ["CPI"]}},
            {"code": "Liður", "selection": {"filter": "item", "values": ["index", "change_M"]}}
        ],
        "response": {"format": "json"}
    }
    resp = requests.post(url, json=payload)
    resp.raise_for_status()
    return resp.json()

def parse_data(js):
    records = []
    for entry in js["data"]:
        date_str, _, measure_type = entry["key"]
        value = entry["values"][0]
        if value != ".":
            try:
                date = datetime.strptime(date_str, "%YM%m")
                records.append({
                    "date": date,
                    "type": measure_type,
                    "value": float(value)
                })
            except ValueError:
                continue
    df = pd.DataFrame(records)
    df_pivot = df.pivot(index="date", columns="type", values="value").sort_index()
    df_pivot = df_pivot.rename(columns={"index": "CPI", "change_M": "Monthly Change"})
    return df_pivot.reset_index()

def compute_trend(df, months_predict=6):
    X = np.arange(len(df)).reshape(-1, 1)
    y = df["CPI"].values
    model = LinearRegression()
    model.fit(X, y)

    future_X = np.arange(len(df), len(df) + months_predict).reshape(-1, 1)
    preds = model.predict(future_X)

    last_date = df["date"].iloc[-1]
    future_dates = [last_date + relativedelta(months=i) for i in range(1, months_predict + 1)]
    return model, list(zip(future_dates, preds))

def compute_annual_cpi(df, end_index):
    if end_index < 12:
        return None
    current = df.loc[end_index, "CPI"]
    prior = df.loc[end_index - 12, "CPI"]
    return (current / prior - 1) * 100

def main():
    raw = fetch_cpi_data()
    df = parse_data(raw)
    df24 = df.tail(24).reset_index(drop=True)

    # Plot CPI
    plt.figure(figsize=(10, 6))
    plt.plot(df24["date"], df24["CPI"], marker='o', label="CPI index")

    trend_model, futures = compute_trend(df24, months_predict=6)
    future_dates, future_vals = zip(*futures)
    plt.plot(future_dates, future_vals, '--', color='red', label="Trend projection")

    plt.title("CPI Index and Trend Projection (Last 24 months + next 6)")
    plt.xlabel("Date")
    plt.ylabel("CPI Index")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    curr_annual = compute_annual_cpi(df24, end_index=len(df24) - 1)
    print(f"Current 12‑month CPI inflation ≈ {curr_annual:.2f}%")
    print(f"Current monthly inflation ≈ {df24.tail(1)["Monthly Change"].values[0]:.2f}%")
    
    extended = pd.concat([df24, pd.DataFrame({
        "date": future_dates,
        "CPI": future_vals
    })], ignore_index=True)

    future_annual = []
    for i in range(len(df24), len(extended)):
        ann = compute_annual_cpi(extended, i)
        future_annual.append((extended.loc[i, "date"], ann))

    print("Projected annual CPI for next 6 months:")
    for i in range(len(df24), len(extended)):
        dropped_index = i - 12
        dropped_date = extended.loc[dropped_index, "date"]
        dropped_pct = extended.loc[dropped_index, "Monthly Change"]
        ann = compute_annual_cpi(extended, i)
        prediction_date = extended.loc[i, "date"]
        print(f"{prediction_date.strftime('%Y-%m')}: {ann:.2f}% "
              f"(Dropped {dropped_date.strftime('%Y-%m')} Monthly %: {dropped_pct:.2f}%)")

    # Compute monthly change stats
    now = pd.Timestamp.now()
    thresholds = {
        "Last 24 months": df["date"] > (now - pd.DateOffset(months=24)),
        "Since 2010": df["date"] >= pd.Timestamp("2010-01-01"),
        "Since 2000": df["date"] >= pd.Timestamp("2000-01-01"),
        "All time": df["Monthly Change"].notna()
    }

    print("\nAverage and Median Monthly Inflation Change:")
    for label, condition in thresholds.items():
        sub = df.loc[condition, "Monthly Change"].dropna()
        if not sub.empty:
            avg = sub.mean()
            med = sub.median()
            print(f"{label:<18} | Avg: {avg:.2f}% | Median: {med:.2f}%")
        else:
            print(f"{label:<18} | Not enough data")


if __name__ == "__main__":
    main()
