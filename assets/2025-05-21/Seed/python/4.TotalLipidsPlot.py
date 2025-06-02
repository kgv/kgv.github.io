import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Data for Table 1
data1 = {
    'Семя': ['Семена(1 mm)', 'Семена(2 mm)', 'Семена(4 mm)', 'Семена(6 mm)', 'Семена(7 mm)', 'Семена(8 mm)', 'Семена(9 mm)', 'Семена(10 mm)', 'Семена(цвет0)', 'Семена(цвет1)', 'Семена(сухие)'],
    'Масса, mg/g': [6.7147, 6.6391, 6.4313, 9.0809, 16.9131, 17.4795, 20.8487, 70.6380, 115.0478, 98.2474, 21.3468],
    'Погрешность': [1.4527, 0.3830, 0.5657, 0.5115, 0.6681, 1.2531, 5.2386, 22.6452, 19.0192, 9.7870, 2.2821]
}
df1 = pd.DataFrame(data1)

# Data for Table 2
data2 = {
    'Семя': ['Семена(1 mm)', 'Семена(2 mm)', 'Семена(4 mm)', 'Семена(6 mm)', 'Семена(7 mm)', 'Семена(8 mm)', 'Семена(9 mm)', 'Семена(10 mm)', 'Семена(цвет0)', 'Семена(цвет1)', 'Семена(сухие)'],
    'Масса, mg/g': [42.6040, 43.7768, 42.7048, 57.3003, 100.2943, 97.5729, 93.0378, 255.1031, 248.5250, 258.2521, 318.1042],
    'Погрешность': [8.5007, 3.0683, 4.5465, 3.7596, 3.4500, 11.9580, 20.2730, 80.0829, 37.4690, 38.3970, 17.2599]
}
df2 = pd.DataFrame(data2)

# Data for Table 3
data3 = {
    'ID': ['Семена(1 мм)', 'Семена(2 мм)', 'Семена(4 мм)', 'Семена(6 мм)', 'Семена(7 мм)', 'Семена(8 мм)', 'Семена(9 мм)', 'Семена(10 мм)', 'Семена(цвет0)', 'Семена(цвет1)', 'Семена(сухие)'],
    'Масса, g': [0.04729044, 0.16744626, 0.523987896, 1.273785669, 2.829302203, 3.891207252, 4.915186974, 17.811298442, 16.144184, 17.943355908, 13.5712794846]
}
df3 = pd.DataFrame(data3)

# Data for Table 4
data4 = {
    'ID': ['Семена(1 мм)', 'Семена(2 мм)', 'Семена(4 мм)', 'Семена(6 мм)', 'Семена(7 мм)', 'Семена(8 мм)', 'Семена(9 мм)', 'Семена(10 мм)', 'Семена(цвет0)', 'Семена(цвет1)', 'Семена(сухие)'],
    'Масса, g': [0.001110, 0.003825, 0.012270, 0.022230, 0.028210, 0.039880, 0.052830, 0.069820, 0.064960, 0.069480, 0.042663],
    'Погрешность': [0.000020, 0.000465, 0.000560, 0.001460, 0.001640, 0.005710, 0.001690, 0.003780, 0.003120, 0.003100, 0.001493]
}
df4 = pd.DataFrame(data4)

# Create first figure with two subplots
fig1, axes1 = plt.subplots(nrows=2, ncols=1, figsize=(12, 10))
plt.style.use('seaborn-v0_8-whitegrid') # Using a seaborn style for better aesthetics

# Plot 1: Масса суммарных липидов на грамм сырого веса
axes1[0].bar(df1['Семя'], df1['Масса, mg/g'], yerr=df1['Погрешность'], capsize=5, color='skyblue', edgecolor='black', alpha=0.7)
axes1[0].plot(df1['Семя'], df1['Масса, mg/g'], marker='o', linestyle='-', color='darkblue', markersize=5)
axes1[0].set_title('Масса суммарных липидов на грамм сырого веса', fontsize=14)
axes1[0].set_ylabel('Масса, mg/g', fontsize=12)
axes1[0].tick_params(axis='x', rotation=45, labelsize=10)
axes1[0].grid(True, linestyle='--', alpha=0.7)
# axes1[0].legend() # Removed legend

# Plot 2: Масса суммарных липидов на грамм сухого веса
axes1[1].bar(df2['Семя'], df2['Масса, mg/g'], yerr=df2['Погрешность'], capsize=5, color='lightcoral', edgecolor='black', alpha=0.7)
axes1[1].plot(df2['Семя'], df2['Масса, mg/g'], marker='o', linestyle='-', color='darkred', markersize=5)
axes1[1].set_title('Масса суммарных липидов на грамм сухого веса', fontsize=14)
axes1[1].set_ylabel('Масса, mg/g', fontsize=12)
axes1[1].tick_params(axis='x', rotation=45, labelsize=10)
axes1[1].grid(True, linestyle='--', alpha=0.7)
# axes1[1].legend() # Removed legend

plt.tight_layout() # Adjust layout to prevent overlapping titles/labels
plt.show()

# Create second figure with two subplots
fig2, axes2 = plt.subplots(nrows=2, ncols=1, figsize=(12, 10))

# Plot 3: Масса суммарных липидов на одно семя
axes2[0].bar(df3['ID'], df3['Масса, g'], capsize=5, color='lightgreen', edgecolor='black', alpha=0.7)
axes2[0].plot(df3['ID'], df3['Масса, g'], marker='o', linestyle='-', color='darkgreen', markersize=5)
axes2[0].set_title('Масса суммарных липидов на одно семя', fontsize=14)
axes2[0].set_ylabel('Масса, g', fontsize=12)
axes2[0].tick_params(axis='x', rotation=45, labelsize=10)
axes2[0].grid(True, linestyle='--', alpha=0.7)
# axes2[0].legend() # Removed legend

# Plot 4: Масса семени
axes2[1].bar(df4['ID'], df4['Масса, g'], yerr=df4['Погрешность'], capsize=5, color='gold', edgecolor='black', alpha=0.7)
axes2[1].plot(df4['ID'], df4['Масса, g'], marker='o', linestyle='-', color='darkgoldenrod', markersize=5)
axes2[1].set_title('Масса семени', fontsize=14)
axes2[1].set_ylabel('Масса, g', fontsize=12)
axes2[1].tick_params(axis='x', rotation=45, labelsize=10)
axes2[1].grid(True, linestyle='--', alpha=0.7)
# axes2[1].legend() # Removed legend

plt.tight_layout()
plt.show()
