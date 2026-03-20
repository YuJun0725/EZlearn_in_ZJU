import matplotlib.pyplot as plt
import matplotlib
import numpy as np
import os

matplotlib.rcParams['font.family'] = ['SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False

# ── 数据 ──────────────────────────────────────────────
# 表2：原始含源二端网络外特性
orig_I = [25.83, 19.85, 16.21, 10.38, 5.60, 0.0]   # mA
orig_U = [0.0,    1.995,  3.241,  5.196,  6.78,  8.68]  # V

# 表3：戴维宁等效电路外特性
thev_I = [25.28, 19.55, 16.04, 10.23, 5.57, 0.0]    # mA
thev_U = [0.0,    1.959,  3.183,  5.139,  6.72,  8.70]  # V

# 表4：诺顿等效电路外特性
nort_I = [25.58, 19.81, 16.19, 10.40, 5.64, 0.0]   # mA
nort_U = [0.0,    1.979,  3.215,  5.190,  6.80,  8.74]  # V

# ── 绘图配置 ──────────────────────────────────────────
os.makedirs('figures', exist_ok=True)

plots = [
    (orig_I, orig_U, 'o-',  'steelblue', '原始含源二端网络外特性', 'figures/orig_char.png'),
    (thev_I, thev_U, 's--', 'tomato',    '戴维宁等效电路外特性',   'figures/thev_char.png'),
    (nort_I, nort_U, '^:',  'seagreen',  '诺顿等效电路外特性',     'figures/nort_char.png'),
]

for I_data, U_data, style, color, title, fname in plots:
    I_arr = np.array(I_data)
    U_arr = np.array(U_data)

    # 线性拟合 U = k*I + b
    k, b = np.polyfit(I_arr, U_arr, 1)
    I_fit = np.linspace(0, max(I_arr), 200)
    U_fit = k * I_fit + b

    # 输出拟合结果
    print(f'\n[拟合] {title}')
    print(f'  U_AB = {k:.4f} * I_R + {b:.4f}')
    print(f'  => 断路电压 U_OC = {b:.4f} V  (令 I_R = 0)')
    print(f'  => 短路电流 I_SC = {-b/k:.4f} mA  (令 U_AB = 0)')
    print(f'  => 等效内阻  R0  = {-k*1000:.2f} Ω  (|k| * 1000)')

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(I_arr, U_arr, style, color=color, linewidth=1.8, markersize=6, label='实测数据')
    ax.plot(I_fit, U_fit, '-', color='gray', linewidth=1.2, linestyle='--',
            label=f'$U_{{AB}}={k:.3f}\\cdot I_R+{b:.3f}$')
    ax.set_xlabel(r'$I_R\ /\ \mathrm{mA}$', fontsize=12)
    ax.set_ylabel(r'$U_{{AB}}\ /\ \mathrm{{V}}$', fontsize=12)
    ax.set_title(title, fontsize=13)
    ax.legend(fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    ax.set_xlim(-1, 28)
    ax.set_ylim(-0.3, 10)
    plt.tight_layout()
    fig.savefig(fname, dpi=200)
    print(f'已保存: {fname}')
    plt.show()
