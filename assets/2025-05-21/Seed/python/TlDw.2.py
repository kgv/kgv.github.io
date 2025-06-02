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

# Parse the mass data and filter out 'Семена(цвет2)'
lines = mass_data_string.strip().split('\n')
mass_data_rows = []
id_to_remove = "Семена(цвет2)"

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
# This list should have 11 dates, matching the number of rows in df_mass after filtering
collection_dates_list = [
    "01 июнь", "07 июнь", "10 июнь", "17 июнь", "27 июнь", 
    "25 июнь", "01 июль", "04 июль", "17 июль", "17 июль", 
    "31 июль"
]

# Assign the provided list of dates directly to the DataFrame
if len(collection_dates_list) == len(df_mass):
    df_mass['Дата сбора'] = collection_dates_list
else:
    # Fallback or error handling if lengths don't match, though they should
    print(f"Warning: Length of provided dates ({len(collection_dates_list)}) does not match data points ({len(df_mass)}). Using empty dates.")
    df_mass['Дата сбора'] = [''] * len(df_mass)


# Create the line plot with error bars
fig, ax = plt.subplots(figsize=(16, 10)) 

# Using plt.errorbar to plot line with error bars
ax.errorbar(df_mass['ID'], df_mass['Масса'], yerr=df_mass['Ошибка'], fmt='-o', capsize=5, color='dodgerblue', ecolor='dimgray', markersize=8, linestyle='-', linewidth=2, label='Масса семян')

# Add labels and title (in Russian)
ax.set_xlabel("Степень созревания семени, мм\nДата сбора") 
ax.set_ylabel("Масса, мг/г")
ax.set_title("Зависимость содержания суммарных липидов на грамм сухой массы от размера семян")

# Create new x-tick labels with ID and Date for the filtered data
new_xticklabels = [f"{id_val}\n{date_val}" for id_val, date_val in zip(df_mass['ID'], df_mass['Дата сбора'])]
ax.set_xticks(range(len(df_mass['ID']))) 
ax.set_xticklabels(new_xticklabels, rotation=45, ha="right", fontsize=9)


# Add a grid for the y-axis
ax.grid(axis='y', linestyle='--', alpha=0.7)

# Add a legend
ax.legend(loc='upper left')

# Adjust layout to prevent labels from being cut off
plt.subplots_adjust(bottom=0.25) 
plt.tight_layout() 

# Display the plot
plt.show()
