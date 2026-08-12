# 《系统动力学（振动）》Lecture 03 课程要点总结

本文根据 `ZJU_Vibration_Lecture03_SDOF_ForcedVib_Non-periodic_2026(2).pdf` 整理。本讲主题是**单自由度系统（SDOF）在非周期激励下的强迫响应**，核心工具是单位冲激响应、阶跃/斜坡响应、卷积积分（Duhamel 积分）以及傅里叶积分。

## 1. 非周期激励的特点

有阻尼 SDOF 的基本方程为

$$
m\ddot{x}(t)+c\dot{x}(t)+kx(t)=F(t).
$$

与简谐或周期激励不同，非周期载荷（冲击、脉冲、任意时间历程等）通常具有以下特点：

- 响应是随时间变化的瞬态过程，通常没有可长期保留的稳态周期响应；
- 载荷可能包含多个频率成分，直接假设单一正弦响应一般不适用；
- 可采用时域卷积/半解析方法，也可采用拉普拉斯变换、傅里叶变换或数值积分方法；
- 线性系统仍满足叠加原理，可把复杂载荷分解为许多简单载荷分别求响应后相加。

## 2. 三种基本输入函数

### 2.1 Dirac 单位冲激

单位冲激（Dirac delta）满足

$$
\int_{-\infty}^{\infty}\delta(t-a)\,\mathrm{d}t=1,
\qquad F(t)=\hat F\,\delta(t-a).
$$

它的持续时间趋于零、面积保持为 1；因此 $\hat F$ 的量纲是冲量（力×时间），而不是普通力的量纲。

对单位冲激输入、零初始条件，定义物理位移冲激响应 $g(t)$：

$$
m\ddot g+c\dot g+kg=\delta(t).
$$

对欠阻尼系统（$\zeta<1$）：

$$
g(t)=\frac{1}{m\omega_d}e^{-\zeta\omega_n t}\sin(\omega_d t)u(t),
\qquad \omega_d=\omega_n\sqrt{1-\zeta^2}.
$$

其中 $u(t)$ 是单位阶跃函数，保证因果性（$t<0$ 时响应为零）。

### 2.2 单位阶跃

$$
u(t-a)=
\begin{cases}
0,&t<a,\\
1,&t>a,
\end{cases}
\qquad
u(t-a)=\int_{-\infty}^{t}\delta(\tau-a)\,\mathrm{d}\tau.
$$

阶跃响应是冲激响应的积分。对有阻尼 SDOF 的恒定单位力输入，物理位移阶跃响应为

$$
s(t)=\frac{1}{k}\left[1-e^{-\zeta\omega_n t}
\left(\cos\omega_d t+\frac{\zeta\omega_n}{\omega_d}\sin\omega_d t\right)\right]u(t)
$$

（欠阻尼情形）。它的长期值为 $1/k$，即静态柔度。

### 2.3 单位斜坡

$$
r(t-a)=(t-a)u(t-a)=\int_{-\infty}^{t}u(\tau-a)\,\mathrm{d}\tau,
\qquad u(t-a)=\frac{\mathrm d}{\mathrm dt}r(t-a).
$$

斜坡响应是阶跃响应的再次积分。欠阻尼 SDOF 的物理斜坡响应为

$$
r_s(t)=\frac{1}{k}\left[t-\frac{2\zeta}{\omega_n}
+e^{-\zeta\omega_n t}\left(\frac{2\zeta}{\omega_n}\cos\omega_d t
+\frac{2\zeta^2-1}{\omega_d}\sin\omega_d t\right)\right]u(t).
$$

这里用 $r_s(t)$ 表示“系统的斜坡响应”，以免与频率比 $r=\omega/\omega_n$ 混淆。

## 3. 用基本响应构造有限时长载荷

### 3.1 矩形脉冲

长度为 $T$、幅值为 $F_0$ 的矩形脉冲可写成

$$
F(t)=F_0\,[u(t)-u(t-T)].
$$

由线性叠加，响应为

$$
x(t)=F_0\,[s(t)-s(t-T)].
$$

对无阻尼系统（$m\ddot x+kx=F(t)$），有

$$
x(t)=\frac{F_0}{k}\left\{[1-\cos(\omega_n t)]u(t)
-[1-\cos(\omega_n(t-T))]u(t-T)\right\}.
$$

力在 $t=T$ 停止后，第二项相当于叠加一个延迟的反向阶跃，响应转为自由振动。

### 3.2 一般构造原则

- 阶跃差可表示矩形脉冲；
- 斜坡差与阶跃项组合可表示梯形或三角脉冲；
- 复杂载荷可先分解，再对每个分量调用对应的基本响应函数。

## 4. 卷积积分（冲激响应法）

将任意载荷在小时间段 $\Delta\tau$ 内近似为冲激：

$$
F(t)\approx\sum F(\tau)\Delta\tau\,\delta(t-\tau).
$$

由延迟冲激响应叠加，零初始条件下的响应为

$$
\boxed{x(t)=\int_{0}^{t}F(\tau)g(t-\tau)\,\mathrm d\tau}
$$

也可写成对称形式

$$
x(t)=\int_{0}^{t}F(t-\lambda)g(\lambda)\,\mathrm d\lambda.
$$

要点：

- $g(t-\tau)$ 是在时刻 $\tau$ 施加的冲激对当前时刻 $t$ 的贡献；
- 积分上限为 $t$，体现因果性；
- 两个形式数学等价，实际计算时可选择移位后更简单的函数；
- 有非零初始条件时，应在卷积结果之外叠加由初始位移、初始速度产生的自由响应。

## 5. Duhamel 积分（阶跃响应法）

把任意载荷看作许多小阶跃的叠加。若 $s(t)$ 是单位阶跃响应，则

$$
x(t)=F(0)s(t)+\int_{0}^{t}\dot F(\tau)s(t-\tau)\,\mathrm d\tau.
$$

这就是 Duhamel 积分的常用形式。对力历程足够光滑时，它与冲激卷积完全等价；形式选择取决于 $F(t)$、$s(t)$ 哪一个更容易积分。

特别地，若输入本身是单位阶跃，则

$$
x(t)=\int_0^t g(\tau)\,\mathrm d\tau=s(t).
$$

## 6. 三角/梯形脉冲算例（无阻尼）

考虑

$$
\ddot x+\omega_n^2x=\frac{F(t)}{m},
$$

其中载荷为梯形脉冲

$$
F(t)=
\begin{cases}
\dfrac{2F_0}{T}t,&0<t<T/2,\\
F_0,&T/2<t<3T/2,\\
\dfrac{2F_0}{T}(2T-t),&3T/2<t<2T,\\
0,&t>2T.
\end{cases}
$$

无阻尼冲激响应为 $g(t)=\sin(\omega_n t)/(m\omega_n)\,u(t)$。卷积积分的关键是根据 $t$ 所在区间确定有效积分范围：

$$
x(t)=
\begin{cases}
\displaystyle \frac{2F_0}{kT}\left(t-\frac{\sin\omega_n t}{\omega_n}\right),
&0<t<T/2,\\[1.2em]
\displaystyle \frac{2F_0}{kT\omega_n}\left[\frac{\omega_nT}{2}
+\sin\omega_n\left(t-\frac T2\right)-\sin\omega_n t\right],
&T/2<t<3T/2,\\[1.2em]
\displaystyle \frac{2F_0}{kT\omega_n}\left[\omega_n(2T-t)
+\sin\omega_n\left(t-\frac T2\right)
+\sin\omega_n\left(t-\frac{3T}{2}\right)-\sin\omega_n t\right],
&3T/2<t<2T,\\[1.2em]
\displaystyle \frac{2F_0}{kT\omega_n}\left[-\sin\omega_n t
+\sin\omega_n\left(t-\frac T2\right)
+\sin\omega_n\left(t-\frac{3T}{2}\right)
-\sin\omega_n(t-2T)\right],
&t>2T.
\end{cases}
$$

在 $t>2T$ 时外力已为零，最后一段响应必然是自由振动。该算例的主要训练点不是死记分段式，而是掌握“载荷支撑区间与延迟冲激响应的重叠范围”如何决定积分上下限。

## 7. 傅里叶积分：从周期到非周期

### 7.1 周期信号的复指数级数

周期信号可展开为

$$
f(t)=\sum_{p=-\infty}^{\infty}C_p e^{ip\omega_0t},
\qquad \omega_0=\frac{2\pi}{T},
$$

其中

$$
C_p=\frac1T\int_{-T/2}^{T/2}f(t)e^{-ip\omega_0t}\,\mathrm dt.
$$

若 $f(t)$ 为实函数，则 $C_{-p}=C_p^*$。

### 7.2 非周期信号的傅里叶变换

令周期 $T\to\infty$，离散频率间隔趋于零，得到变换对

$$
\hat f(\omega)=\int_{-\infty}^{\infty}f(t)e^{-i\omega t}\,\mathrm dt,
$$

$$
f(t)=\frac{1}{2\pi}\int_{-\infty}^{\infty}\hat f(\omega)e^{i\omega t}\,\mathrm d\omega.
$$

对归一化 SDOF

$$
\ddot x+2\zeta\omega_n\dot x+\omega_n^2x=\omega_n^2f(t),
$$

若归一化传递函数为

$$
G(\omega)=\frac{\omega_n^2}
{\omega_n^2-\omega^2+i2\zeta\omega_n\omega},
$$

则非周期响应可写为

$$
\boxed{x(t)=\frac{1}{2\pi}\int_{-\infty}^{\infty}
\hat f(\omega)G(\omega)e^{i\omega t}\,\mathrm d\omega}.
$$

频域中“输入谱 × 传递函数 = 输出谱”：

$$
X(\omega)=\hat f(\omega)G(\omega).
$$

时域卷积与频域乘法是同一线性系统关系的两种表达。

## 8. 拉普拉斯变换与传递函数

对零初始条件，归一化 SDOF 的传递函数为

$$
H(s)=\frac{\omega_n^2}{s^2+2\zeta\omega_n s+\omega_n^2}.
$$

分母的根（极点）是系统特征根，决定响应的衰减与振荡性质：

- $\zeta<1$：共轭复极点，冲激响应为衰减正弦；
- $\zeta=1$：重根，冲激响应为 $\omega_n^2t e^{-\omega_n t}$；
- $\zeta>1$：两个负实极点，冲激响应是两个指数衰减项之差。

归一化冲激响应 $h(t)=\mathcal L^{-1}\{H(s)\}$ 为

$$
h(t)=
\begin{cases}
\displaystyle \frac{\omega_n}{\sqrt{1-\zeta^2}}e^{-\zeta\omega_n t}\sin(\omega_d t)u(t),&\zeta<1,\\[0.8em]
\displaystyle \frac{ab}{b-a}\left(e^{-at}-e^{-bt}\right)u(t),&\zeta>1,\\[0.8em]
\displaystyle \omega_n^2t e^{-\omega_n t}u(t),&\zeta=1,
\end{cases}
$$

其中

$$
a=\omega_n\left(\zeta-\sqrt{\zeta^2-1}\right),
\qquad
b=\omega_n\left(\zeta+\sqrt{\zeta^2-1}\right),
\qquad ab=\omega_n^2.
$$

### 状态空间形式

令 $\mathbf{x}=[x,\dot x]^\mathsf T$，则

$$
\dot{\mathbf{x}}=A\mathbf{x}+Bf(t),
\qquad y=C\mathbf{x}+Df(t),
$$

$$
A=\begin{bmatrix}0&1\\-k/m&-c/m\end{bmatrix},
\qquad B=\begin{bmatrix}0\\1/m\end{bmatrix}.
$$

一般传递函数矩阵为

$$
G(s)=C(sI-A)^{-1}B+D.
$$

## 9. 响应变量会影响“共振峰”

对力输入，位移、速度、加速度频谱的幅值关系为

$$
|V(\omega)|=\omega|X(\omega)|,
\qquad
|A(\omega)|=\omega|V(\omega)|=\omega^2|X(\omega)|.
$$

因此，使用不同响应变量绘制 FRF 时，曲线形状及峰值位置不一定相同；不能把“位移共振频率”直接当作所有测量量的共振频率。

以加速度/力为例：

$$
G_a(j\omega)=\frac{-\omega^2/m}
{\omega_n^2-\omega^2+2i\zeta\omega_n\omega}
=\frac{-r^2/m}{1-r^2+2i\zeta r},
\qquad r=\frac{\omega}{\omega_n}.
$$

其幅值为

$$
|G_a(j\omega)|=\frac{r^2/m}
{\sqrt{(1-r^2)^2+(2\zeta r)^2}}.
$$

当 $\zeta<1/\sqrt2$ 时，加速度幅值峰值出现在

$$
r=\frac{1}{\sqrt{1-2\zeta^2}},
$$

峰值为

$$
|G_a|_{\max}=\frac{1}{2m\zeta\sqrt{1-\zeta^2}}.
$$
