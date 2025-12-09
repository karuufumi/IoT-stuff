import requests
import numpy as np
from sklearn.linear_model import LinearRegression
from datetime import datetime, timedelta

# ============================================================
# ADAFRUIT IO CONFIG  (must match your gateway)
# ============================================================
AIO_USERNAME = "ntk_cse"
AIO_KEY      = "rwJ51Y6x1c4VLCA"

FEED_RT  = "rt"
FEED_RH  = "rh"
FEED_LUX = "lux"

BASE_URL = f"https://io.adafruit.com/api/v2/{AIO_USERNAME}/feeds"



# ============================================================
# HELPERS — fetch data from Adafruit IO
# ============================================================
def fetch_feed(feed_key, limit=100):
    """
    Fetch latest data points from an Adafruit IO feed.
    Returns a list of (timestamp, value).
    """
    url = f"{BASE_URL}/{feed_key}/data?limit={limit}"
    headers = {"X-AIO-Key": AIO_KEY}

    r = requests.get(url, headers=headers)
    r.raise_for_status()

    items = r.json()
    data = []

    for row in items:
        ts = datetime.fromisoformat(row["created_at"].replace("Z", "+00:00"))
        val = float(row["value"])
        data.append((ts, val))

    data.reverse()  # oldest → newest
    return data


# ============================================================
# Build regression model
# ============================================================
def train_regression(time_value_pairs):
    """
    time_value_pairs = list of (timestamp, value)
    Convert timestamps to seconds relative to t0.
    Fit LinearRegression.
    """
    if len(time_value_pairs) < 3:
        raise Exception("Not enough data to train regression.")

    t0 = time_value_pairs[0][0]
    X = np.array([(t - t0).total_seconds() for (t, v) in time_value_pairs]).reshape(-1, 1)
    y = np.array([v for (t, v) in time_value_pairs])

    model = LinearRegression()
    model.fit(X, y)

    return model, t0


# ============================================================
# Predict value N minutes into the future
# ============================================================
def predict_future(model, t0, minutes=5):
    """
    Predict value N minutes into the future.
    """
    future_time = t0 + timedelta(minutes=minutes)
    delta_sec = (future_time - t0).total_seconds()
    pred = model.predict(np.array([[delta_sec]]))
    return pred[0]


# ============================================================
# High-level pipeline
# ============================================================
def run_prediction(feed_key="rt", limit=60, minutes_ahead=10):
    """
    1. Fetch data
    2. Train regression
    3. Predict future
    """

    print(f"Fetching feed '{feed_key}'...")
    data = fetch_feed(feed_key, limit=limit)

    print(f"Training regression on {len(data)} samples...")
    model, t0 = train_regression(data)

    print(f"Predicting {minutes_ahead} minutes ahead...")
    prediction = predict_future(model, t0, minutes_ahead=minutes_ahead)

    print(f"\n📈 Prediction for '{feed_key}' {minutes_ahead} minutes ahead:")
    print(f"→ {prediction:.2f}")

    return prediction


# ============================================================
# Standalone test
# ============================================================
if __name__ == "__main__":
    # Example: predict RT 15 minutes ahead
    run_prediction(feed_key=FEED_RT, limit=80, minutes_ahead=15)
