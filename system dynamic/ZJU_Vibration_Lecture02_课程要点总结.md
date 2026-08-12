# 《系统动力学（振动）》Lecture 02 课程要点总结

本文根据 `ZJU_Vibration_Lecture02_SDOF_ForcedVib_Harmonic_2026.pdf` 整理，主题是**单自由度系统（SDOF）的强迫振动响应**，并延伸到基座激励、传递函数、阻尼识别和周期激励。

## 1. 问题定义与激励分类

有阻尼 SDOF 在外力作用下的运动方程为

$$
m\ddot{x}+c\dot{x}+kx=F(t),\qquad x(0)=x_0,\quad \dot{x}(0)=v_0.
$$

外部激励可按频谱结构分为：

- **简谐激励（harmonic excitation）**：单一频率，例如 $(F(t)=F_0\cos(\omega t+\phi))$；
- **周期激励（periodic excitation）**：含基频及多个谐波；
- **非周期激励（non-periodic excitation）**：一般时间函数或冲击，需要时域/数值方法处理。

## 2. 简谐强迫响应

以 (F(t)=F_0\cos\omega t) 为例，总响应可以分解为

$$
x(t)=x_h(t)+x_p(t).
$$

- (x_h(t)) 是**齐次响应/自由响应**，由初始条件决定；有阻尼时随时间衰减，属于瞬态响应；
- (x_p(t)) 是**特解/稳态响应**，由外部激励决定，激励持续时长期保留。

对于欠阻尼系统，稳态响应写为

$$
x_{ss}(t)=X\cos(\omega t-\phi),
$$

其中

$$
X=\frac{F_0}{\sqrt{(k-m\omega^2)^2+(c\omega)^2}},\qquad
\phi=\operatorname{atan2}(c\omega,\,k-m\omega^2).
$$

定义静态位移 $\delta_{st}=F_0/k$、频率比 $r=\omega/\omega_n$，以及阻尼比

$$
\omega_n=\sqrt{k/m},\qquad \zeta=\frac{c}{2m\omega_n},
$$

则幅值放大系数（magnification factor）为

$$
M=\frac{X}{\delta_{st}}
=\frac{1}{\sqrt{(1-r^2)^2+(2\zeta r)^2}},
$$

相位滞后为

$$
\phi=\operatorname{atan2}(2\zeta r,\,1-r^2).
$$

因此，归一化响应只由 $r$ 和 $\zeta$ 决定。计算相位应使用 `atan2`，避免象限判断错误。

## 3. 共振、峰值与稳定性

- 当 $r\approx1$ 时响应显著放大，可能引起过大应力、疲劳甚至结构失效；阻尼越小，峰值越高、频带越窄。
- 有阻尼时，幅值真正达到峰值的**共振频率**为

  $$
  \omega_r=\omega_n\sqrt{1-2\zeta^2},
  $$

该式要求 $\zeta<1/\sqrt{2}$。它与阻尼固有频率 $\omega_d=\omega_n\sqrt{1-\zeta^2}$ 一般不相同。
- $\omega$ 与 $\omega_n$ 接近但不相等时可能出现拍振（beating）；无阻尼或低阻尼时尤为明显。
- 对于稳定的有阻尼系统，有限输入产生有界输出，称为**有界输入有界输出稳定性（BIBO stability）**；瞬态衰减后只剩稳态响应。

## 4. 频率响应函数与传递函数

将谐波量写成复数形式 $F(t)=\Re\{\hat F e^{i\omega t}\}$、$x(t)=\Re\{\hat X e^{i\omega t}\}$，有

$$
H(i\omega)=\frac{\hat X}{\hat F}
=\frac{1}{k-m\omega^2+i c\omega}
$$

或以 $kA$ 为输入幅值时

$$
G(i\omega)=\frac{\hat X}{A}
=\frac{1}{1-r^2+2i\zeta r}.
$$

频率响应函数（FRF）/传递函数同时包含：

- $|G(i\omega)|$：幅值增益；
- $\angle G(i\omega)$：输入与输出的相位差；
- 分母的极点/奇异点对应系统特征根，决定共振峰和稳定性。

传递函数也可从线性时不变系统的拉普拉斯表达式得到，再令 $s=i\omega$ 转换到频域。

## 5. 基座激励与振动传递率

当支承基座位移为 $y(t)$，质量块绝对位移为 $x(t)$ 时：

$$
m\ddot{x}+c\dot{x}+kx=ky+c\dot{y}.
$$

若 $y(t)=Y\sin\omega t$，稳态位移 $x_p(t)=X\sin(\omega t-\phi)$。位移传递率为

$$
T_d=\frac{X}{Y}
=\frac{\sqrt{1+(2\zeta r)^2}}
{\sqrt{(1-r^2)^2+(2\zeta r)^2}}.
$$

它描述基座运动向质量块的位移传递程度。设计隔振时通常关注高频区的传递率；低阻尼会提高共振区峰值，适当阻尼可降低峰值，但过大的阻尼会削弱高频隔振效果。

## 6. 加速度计与地震仪原理

加速度计测量质量块相对基座的位移 $z=x-y$，其方程为

$$
m\ddot{z}+c\dot{z}+kz=-m\ddot{y}.
$$

相对位移幅值满足

$$
\frac{Z}{Y}=r^2|G(i\omega)|.
$$

在 $r=\omega/\omega_n\ll1$ 时，$|G|\approx1$，于是

$$
-\omega_n^2 z(t)\approx\ddot{y}(t),
$$

相对位移可用来估计基座加速度。相反，在 $r>3$ 的高频比条件下，$Z\approx Y$，相对位移可估计基座位移，体现了地震仪/惯性式位移测量原理。

## 7. 半功率带宽法（Q-factor method）

对数减量法属于自由振动的时域识别；半功率法利用简谐稳态频率响应，可从共振曲线识别阻尼比。

对归一化传递函数

$$
G(i\omega)=\frac{\omega_n^2}{\omega_n^2-\omega^2+i2\zeta\omega_n\omega},
$$

在小阻尼条件下，共振峰值约为 $|G|_{max}\approx1/(2\zeta)$。令 $\omega_1,\omega_2$ 为幅值降至峰值 $1/\sqrt{2}$ 的两个半功率频率，带宽 $\Delta\omega=\omega_2-\omega_1$，则

$$
\zeta\approx\frac{\Delta\omega}{2\omega_n}
\approx\frac{\omega_2-\omega_1}{\omega_2+\omega_1},
\qquad
Q=\frac{\omega_n}{\Delta\omega}\approx\frac{1}{2\zeta}.
$$

带宽越窄，$Q$ 越大，系统阻尼越小、共振越尖锐。

## 8. 转动不平衡与轴系涡动

转子质量偏心 $e$ 会产生与 $\omega^2$ 成正比的简谐不平衡力。其响应可直接用 FRF 表示，且峰值通常出现在 $\omega>\omega_n$，高频时归一化 FRF 幅值趋近于 1。

对于带偏心圆盘的转轴，横向 $x,y$ 方向可分别写成标准 SDOF 方程。圆截面且两个方向参数相同的情况下为**同步涡动（synchronous whirl）**；无阻尼且两个方向固有频率不同时为**异步涡动（asynchronous whirling）**，质心轨迹为椭圆。穿越 $\omega_{nx}$ 或 $\omega_{ny}$ 时会发生临界转速现象，椭圆旋转方向可能改变。

## 9. 结构阻尼与周期激励

除黏性阻尼和库仑阻尼外，材料内部摩擦也会造成**结构阻尼（structural damping）**，其本质是循环应力下的滞回损耗。常用复刚度表示：

$$
k^*=k(1+i\gamma),
\qquad
G^*(\omega)=\frac{1}{1-(\omega/\omega_n)^2+i\gamma}.
$$

任意周期激励可按傅里叶级数分解：

$$
f(t)=\frac{a_0}{2}+\sum_{p=1}^{\infty}\left[a_p\cos(p\omega_0t)+b_p\sin(p\omega_0t)\right],
\qquad \omega_0=\frac{2\pi}{T}.
$$

线性系统可对每个谐波分别求稳态响应，再按**叠加原理（superposition principle）**相加。某一谐波 $p\omega_0$ 接近固有频率时，该谐波可能主导总响应，因此周期激励分析的关键是识别各谐波与系统 FRF 的匹配关系。

## 10. MATLAB 与复习重点

- 对简谐激励，先计算 $\omega_n,\zeta,r,\omega_d$，再用 FRF 求幅值和相位；
- 对基座激励，先明确绝对坐标 $x$、基座坐标 $y$ 和相对坐标 $z=x-y$；
- 用 `atan2` 计算相位，用 `fzero` 或 `roots` 求阻尼识别方程；
- 以频率扫描绘制 $|G(i\omega)|$、相位和传递率曲线，读取共振频率和半功率带宽；
- 周期信号用傅里叶系数截断展开，比较保留 $N=1,2,5$ 个谐波时的响应收敛性。

应掌握的主线是：**激励分类 → 建立运动方程 → 分解瞬态/稳态响应 → 用 FRF 分析幅值和相位 → 识别共振、传递率和阻尼 → 解释工程测量与隔振现象**。
