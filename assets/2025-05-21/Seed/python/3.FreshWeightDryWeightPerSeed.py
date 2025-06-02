import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Data for Table 5: Масса сырого семени
data5 = {
    'ID': ['Семена(1 мм)', 'Семена(2 мм)', 'Семена(4 мм)', 'Семена(6 мм)', 'Семена(7 мм)', 'Семена(8 мм)', 'Семена(9 мм)', 'Семена(10 мм)', 'Семена(цвет0)', 'Семена(цвет1)', 'Семена(сухие)'],
    'Масса, мг': [1.110, 3.825, 12.270, 22.230, 28.210, 39.880, 52.830, 69.820, 64.960, 69.480, 42.663],
    'Погрешность': [0.020, 0.465, 0.560, 1.460, 1.640, 5.710, 1.690, 3.780, 3.120, 3.100, 1.493]
}
df5 = pd.DataFrame(data5)

# Data for Table 6: Масса сухого семени
data6 = {
    'ID': ['Семена(1 мм)', 'Семена(2 мм)', 'Семена(4 мм)', 'Семена(6 мм)', 'Семена(7 мм)', 'Семена(8 мм)', 'Семена(9 мм)', 'Семена(10 мм)', 'Семена(цвет0)', 'Семена(цвет1)', 'Семена(сухие)'],
    'Масса, мг': [0.175, 0.580, 1.850, 3.520, 4.760, 7.200, 11.820, 19.310, 25.000, 27.080, 25.043],
    'Погрешность': [0.005, 0.065, 0.060, 0.200, 0.290, 1.380, 1.100, 0.390, 1.740, 1.780, 1.050]
}
df6 = pd.DataFrame(data6)

# Create third figure with two subplots
fig3, axes3 = plt.subplots(nrows=2, ncols=1, figsize=(12, 10))
plt.style.use('seaborn-v0_8-whitegrid') # Using a seaborn style for better aesthetics

# Plot 5: Масса сырого семени
axes3[0].bar(df5['ID'], df5['Масса, мг'], yerr=df5['Погрешность'], capsize=5, color='mediumpurple', edgecolor='black', alpha=0.7)
axes3[0].plot(df5['ID'], df5['Масса, мг'], marker='o', linestyle='-', color='indigo', markersize=5)
axes3[0].set_title('Масса сырого семени', fontsize=14)
axes3[0].set_ylabel('Масса, мг', fontsize=12)
axes3[0].tick_params(axis='x', rotation=45, labelsize=10)
axes3[0].grid(True, linestyle='--', alpha=0.7)

# Plot 6: Масса сухого семени
axes3[1].bar(df6['ID'], df6['Масса, мг'], yerr=df6['Погрешность'], capsize=5, color='lightseagreen', edgecolor='black', alpha=0.7)
axes3[1].plot(df6['ID'], df6['Масса, мг'], marker='o', linestyle='-', color='darkcyan', markersize=5)
axes3[1].set_title('Масса сухого семени', fontsize=14)
axes3[1].set_ylabel('Масса, мг', fontsize=12)
axes3[1].tick_params(axis='x', rotation=45, labelsize=10)
axes3[1].grid(True, linestyle='--', alpha=0.7)

plt.tight_layout() # Adjust layout to prevent overlapping titles/labels
plt.show()
