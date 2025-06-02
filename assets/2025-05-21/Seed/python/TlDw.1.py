import pandas as pd
import matplotlib.pyplot as plt
import io

# Data provided by the user (mass data)
mass_data_string = """
| ID                | Масса, mg/g
| 1 мм              | 42.6040 ±8.5007
| 2 мм              | 43.7768 ±3.0683
| 4 мм              | 42.7048 ±4.5465
| 6 мм              | 57.3003 ±3.7596
| 7 мм              | 100.2943 ±3.4500
| 8 мм              | 97.5729 ±11.9580
| 9 мм              | 93.0378 ±20.2730
| 10 мм             | 255.1031 ±80.0829
| Зелено-коричневые | 248.5250 ±37.4690
| Коричнево-зеленые | 258.2521 ±38.3970
| Сухие             | 318.1042 ±17.2599
"""

# Parse the mass data
lines = mass_data_string.strip().split('\n')
mass_data_rows = []
for line in lines[1:]: # Skip header
    parts = [p.strip() for p in line.strip('|').split('|')]
    id_val = parts[0]
    mass_str = parts[1]
    value_error_pair = mass_str.split('±')
    mean_mass = float(value_error_pair[0].strip())
    error_mass = float(value_error_pair[1].strip())
    mass_data_rows.append({'ID': id_val, 'Масса': mean_mass, 'Ошибка': error_mass})

df_mass = pd.DataFrame(mass_data_rows)

# User-provided list of collection dates
collection_dates_list = [
    "01 июнь", "07 июнь", "10 июнь", "17 июнь", "27 июнь", 
    "25 июнь", "01 июль", "04 июль", "17 июль", "17 июль", 
    "31 июль"
]

if len(collection_dates_list) == len(df_mass):
    df_mass['Дата сбора'] = collection_dates_list
else:
    print(f"Warning: Length of provided dates ({len(collection_dates_list)}) does not match data points ({len(df_mass)}). Using empty dates.")
    df_mass['Дата сбора'] = [''] * len(df_mass)

# --- Function to generate Line Chart ---
def generate_line_plot(df):
    fig, ax = plt.subplots(figsize=(16, 10)) 
    ax.errorbar(df['ID'], df['Масса'], yerr=df['Ошибка'], fmt='-o', capsize=5, color='dodgerblue', ecolor='dimgray', markersize=8, linestyle='-', linewidth=2, label='Масса семян')
    
    ax.set_xlabel("Степень созревания семени, мм\nДата сбора") 
    ax.set_ylabel("Масса, мг/г")
    ax.set_title("Зависимость содержания суммарных липидов от степени созревания семян")

    new_xticklabels = [f"{id_val}\n{date_val}" for id_val, date_val in zip(df['ID'], df['Дата сбора'])]
    ax.set_xticks(range(len(df['ID']))) 
    ax.set_xticklabels(new_xticklabels, rotation=45, ha="right", fontsize=9)

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(loc='upper left')
    plt.subplots_adjust(bottom=0.25) 
    plt.tight_layout() 
    plt.show()

# --- Function to generate Bar Chart ---
def generate_bar_plot(df):
    fig, ax = plt.subplots(figsize=(16, 10))
    ax.bar(df['ID'], df['Масса'], yerr=df['Ошибка'], capsize=5, color='skyblue', edgecolor='black', label='Масса семян')

    ax.set_xlabel("Степень созревания семени, мм\nДата сбора")
    ax.set_ylabel("Масса, мг/г")
    ax.set_title("Зависимость содержания суммарных липидов от степени созревания семян")

    new_xticklabels = [f"{id_val}\n{date_val}" for id_val, date_val in zip(df['ID'], df['Дата сбора'])]
    ax.set_xticks(range(len(df['ID'])))
    ax.set_xticklabels(new_xticklabels, rotation=45, ha="right", fontsize=9)

    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(loc='upper left')
    plt.subplots_adjust(bottom=0.25)
    plt.tight_layout()
    plt.show()

# Generate and display the Line Chart
print("Generating Line Chart:")
generate_line_plot(df_mass.copy()) # Use .copy() if functions modify df, though these don't

# Generate and display the Bar Chart
print("\nGenerating Bar Chart:")
generate_bar_plot(df_mass.copy())

