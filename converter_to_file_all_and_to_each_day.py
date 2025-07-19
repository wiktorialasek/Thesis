# import os
# import pandas as pd

# # Zakres lat (możesz tu podać dowolne liczby)
# start_year = 2005
# end_year = 2020

# # Główna ścieżka
# base_path = r"C:\Users\Fujitsu\Downloads\financial-data-master\financial-data-master\pyfinancialdata\data\currencies\oanda\SPX500_USD"
# out_folder_path = os.path.join(base_path, "all")

# # # Upewnij się, że folder docelowy istnieje
# # os.makedirs(out_folder_path, exist_ok=True)

# # Przetwarzanie lat
# for year in range(start_year, end_year + 1):
#     folder_path = os.path.join(base_path, str(year))
#     if not os.path.exists(folder_path):
#         print(f"Folder dla roku {year} nie istnieje, pomijam...")
#         continue

#     csv_files = [file for file in os.listdir(folder_path) if file.endswith('.csv')]

#     df_list = []
#     for file in sorted(csv_files):
#         file_path = os.path.join(folder_path, file)
#         try:
#             df = pd.read_csv(file_path)
#             df_list.append(df)
#         except Exception as e:
#             print(f"Błąd przy wczytywaniu {file_path}: {e}")

#     if df_list:
#         merged_df = pd.concat(df_list, ignore_index=True)
#         output_file = os.path.join(out_folder_path, f"{year}.csv")
#         merged_df.to_csv(output_file, index=False)
#         print(f"Połączono pliki z roku {year}. Zapisano jako '{year}.csv'")
#     else:
#         print(f"Brak danych do połączenia dla roku {year}.")

import os
import pandas as pd

# Folder wejściowy z rocznymi plikami CSV
input_folder = r"C:\Users\Fujitsu\Downloads\financial-data-master\financial-data-master\pyfinancialdata\data\currencies\oanda\EUR_USD\all"
# Folder wyjściowy z danymi rozdzielonymi na dni
output_folder = os.path.join(input_folder, "split_by_date")

# Upewnij się, że folder docelowy istnieje
os.makedirs(output_folder, exist_ok=True)

# Pobierz wszystkie pliki CSV z folderu "all"
csv_files = [f for f in os.listdir(input_folder) if f.endswith('.csv')]

for file in sorted(csv_files):
    file_path = os.path.join(input_folder, file)
    try:
        df = pd.read_csv(file_path)

        # Sprawdź czy jest kolumna z datą
        if 'time' not in df.columns:
            print(f"Brak kolumny 'time' w {file}, pomijam...")
            continue

        df['time'] = pd.to_datetime(df['time'])

        # Grupowanie po dacie
        df['date'] = df['time'].dt.date

        for date_value, group in df.groupby('date'):
            year = str(date_value.year)
            month = f"{date_value.month:02d}"
            day = f"{date_value.day:02d}"

            # Ścieżka do folderu
            day_folder = os.path.join(output_folder, year, month, day)
            os.makedirs(day_folder, exist_ok=True)

            # Ścieżka do pliku
            output_file = os.path.join(day_folder, f"{year}-{month}-{day}.csv")

            # Zapisz dane tego dnia
            group.drop(columns=['date']).to_csv(output_file, index=False)

        print(f"Plik {file} został rozdzielony na dni.")

    except Exception as e:
        print(f"Błąd podczas przetwarzania {file}: {e}")