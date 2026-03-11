# generate_sample_data.py
import numpy as np
import pandas as pd

N = 3000
np.random.seed(42)
temp = np.random.uniform(5, 45, N)         # °C
humidity = np.random.uniform(5, 100, N)   # %
wind = np.random.uniform(0, 20, N)        # m/s
rain = np.random.exponential(1.5, N)      # mm

# heuristic risk score (toy): higher temp, wind => higher risk, more humidity/rain => lower risk
risk_score = 0.4*temp - 0.35*humidity + 0.35*wind - 0.25*rain + np.random.normal(0,4,N)

# convert to 4 classes using quantiles
labels = pd.qcut(risk_score, q=4, labels=['Low','Moderate','High','Extreme'])

df = pd.DataFrame({
    'temp': temp.round(2),
    'humidity': humidity.round(1),
    'wind': wind.round(2),
    'rainfall': rain.round(2),
    'risk': labels
})
df.to_csv('data/fire_data.csv', index=False)
print("Saved data/fire_data.csv (synthetic).")
