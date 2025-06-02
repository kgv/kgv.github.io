import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Data provided by the user
data = {
    'ID': ['Семена(1 мм)', 'Семена(2 мм)', 'Семена(4 мм)', 'Семена(6 мм)', 'Семена(7 мм)', 'Семена(8 мм)', 'Семена(9 мм)', 'Семена(10 мм)', 'Семена(цвет0)', 'Семена(цвет1)', 'Семена(сухие)'],
    'Масса в сыром весе семени, г': [0.04729044, 0.16744626, 0.523987896, 1.273785669, 2.829302203, 3.891207252, 4.915186974, 17.811298442, 16.144184, 17.943355908, 13.5712794846],
    'Масса в сухом весе семени, г': [0.0074557, 0.025390544, 0.07900388, 0.201697056, 0.477400868, 0.70252488, 1.099706796, 4.926040861, 6.213125, 6.993466868, 7.9662834806]
}

df = pd.DataFrame(data)

# Plotting
plt.figure(figsize=(14, 8))

# Set position of bar on X axis
bar_width = 0.35
r1 = np.arange(len(df['ID']))
r2 = [x + bar_width for x in r1]

# Make the plot
plt.bar(r1, df['Масса в сыром весе семени, г'], color='skyblue', width=bar_width, edgecolor='grey', label='Масса в сыром весе семени, г')
plt.bar(r2, df['Масса в сухом весе семени, г'], color='lightcoral', width=bar_width, edgecolor='grey', label='Масса в сухом весе семени, г')

# Add xticks on the middle of the group bars
plt.xlabel('ID Семени', fontweight='bold', fontsize=12)
plt.ylabel('Масса, г', fontweight='bold', fontsize=12)
plt.xticks([r + bar_width/2 for r in range(len(df['ID']))], df['ID'], rotation=45, ha="right")
plt.title('Масса суммарных липидов на грамм сухого и сырого веса семени', fontsize=15, fontweight='bold')

# Create legend & Show graphic
plt.legend()
plt.tight_layout() # Adjust layout to make room for rotated x-axis labels
plt.grid(axis='y', linestyle='--')
plt.show()
