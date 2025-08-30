import pandas as pd
import matplotlib.pyplot as plt

# Wczytaj dane
df = pd.read_csv(r"C:\Users\Fujitsu\Downloads\TSLA_1min.csv")

# Konwersja kolumny czasu na datetime
df['datetime'] = pd.to_datetime(df['datetime'])

# Filtrowanie tylko 1 maja 2020
day_data = df[df['datetime'].dt.date == pd.to_datetime("2020-05-01").date()]

# Wykres
plt.figure(figsize=(14,6))
plt.plot(day_data['datetime'], day_data['open'], label="TSLA price (adjusted)")

# Dodaj pionową linię dla tweeta 15:11 UTC
plt.axvline(pd.to_datetime("2020-05-01 16:11:00"), color="red", linestyle="--", label="Elon Musk tweet")

plt.title("Tesla (TSLA) price on 2020-05-01 with Musk's tweet marked")
plt.xlabel("Time (UTC)")
plt.ylabel("Price (USD, split-adjusted)")
plt.legend()
plt.grid(True)
plt.show()
