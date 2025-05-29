import matplotlib.pyplot as plt
import numpy as np

# Данные для оси X (ID и даты) - остаются прежними
seed_ids_str = ["С_1", "С_2", "С_4", "С_6", "С_7", "С_8", "С_9", "С_10"]
seed_x_positions = np.array([int(s.split('_')[1]) for s in seed_ids_str])
numerical_ids_labels = [str(x) for x in seed_x_positions]

dates_for_annotation = [
    "01 июня", "07 июня", "10 июня", "17 июня",
    "25 июня", "27 июня", "01 июля", "04 июля"
]
dates_to_use = dates_for_annotation

# НОВЫЕ ДАННЫЕ
# Данные FW (Fresh Weight)
fw_means = np.array([
    0.001110,
    0.003825,
    0.012270,
    0.022230,
    0.028210,
    0.039880,
    0.052830,
    0.069820,
])
fw_errors = np.array([
    0.000020,
    0.000465,
    0.000560,
    0.001460,
    0.001640,
    0.005710,
    0.001690,
    0.003780,
])

# Данные DW (Dry Weight)
dw_means = np.array([
    0.000175,
    0.000580,
    0.001850,
    0.003520,
    0.004760,
    0.007200,
    0.011820,
    0.019310,
])
dw_errors = np.array([
    0.000005,
    0.000065,
    0.000060,
    0.000200,
    0.000290,
    0.001380,
    0.001100,
    0.000390,
])

# Данные DW% (Dry Weight Percentage)
dw_percent_means = np.array([
    15.74,
    15.18,
    15.08,
    15.85,
    16.86,
    17.99,
    22.36,
    27.69,
])
dw_percent_errors = np.array([
    0.20,
    0.25,
    0.29,
    0.18,
    0.42,
    0.94,
    1.67,
    1.04,
])

# Создание фигуры и первой оси (для FW и DW)
fig, ax1 = plt.subplots(figsize=(14, 9)) # Размер оставим прежним, но можно настроить

# График FW на первой оси
color_fw = 'royalblue'
line1 = ax1.errorbar(seed_x_positions, fw_means, yerr=fw_errors, fmt='-o', capsize=5, label='FW (Сырая масса, г)', color=color_fw, markersize=7)
ax1.set_ylabel("Масса, г", color='black')
ax1.tick_params(axis='y', labelcolor='black')

# График DW на первой оси
color_dw = 'forestgreen'
line2 = ax1.errorbar(seed_x_positions, dw_means, yerr=dw_errors, fmt='-s', capsize=5, label='DW (Сухая масса, г)', color=color_dw, markersize=7)

# Настройка оси X: сначала метки ID
ax1.set_xticks(seed_x_positions)
ax1.set_xticklabels(numerical_ids_labels)

# Добавляем даты мелким шрифтом под числовыми ID
y_offset_for_dates = -0.065 # Относительно оси X (0) в координатах оси (подобрано)
date_fontsize = 8
date_color = 'dimgray'

for i, pos in enumerate(seed_x_positions):
    ax1.text(pos, y_offset_for_dates, dates_to_use[i],
             transform=ax1.get_xaxis_transform(),
             ha='center', va='top',
             fontsize=date_fontsize, color=date_color)

# Устанавливаем название оси X С ОТСТУПОМ, чтобы оно было ниже дат
xlabel_text = "Размер семени, мм\nДата сбора"
ax1.set_xlabel(xlabel_text, labelpad=35) # labelpad - расстояние в пунктах

# Создание второй оси Y, разделяющей ту же ось X (для DW%)
ax2 = ax1.twinx()
color_dw_percent = 'orangered'
line3 = ax2.errorbar(seed_x_positions, dw_percent_means, yerr=dw_percent_errors, fmt='-^', capsize=5, label='DW (%)', color=color_dw_percent, markersize=7)
ax2.set_ylabel("Содержание сухой массы, %", color=color_dw_percent)
ax2.tick_params(axis='y', labelcolor=color_dw_percent)

# Добавление общего заголовка
plt.title("Динамика накопления массы и содержания сухой массы в одном семени", pad=20)

# Объединение легенд с обеих осей
lines = [line1, line2, line3]
labels = [l.get_label() for l in lines]
ax1.legend(lines, labels, loc='upper left', bbox_to_anchor=(0.01, 0.98))

# Включение сетки (относится к ax1, но видна на всем графике)
ax1.grid(True, linestyle='--', alpha=0.7)

# Ручная настройка отступов для лучшего размещения всех элементов
plt.subplots_adjust(left=0.08, right=0.92, top=0.92, bottom=0.20)

# Показать график
plt.show()