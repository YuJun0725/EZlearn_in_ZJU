# 《系统动力学（振动）》Lecture 04 课程要点总结

本文根据 ZJU_Vibration_Lecture04_2DOF_FreeVib_2026.pdf 整理。本讲从单自由度系统过渡到**两自由度系统（2DOF）**，核心是矩阵建模、广义特征值问题、固有频率与振型、模态正交性、模态坐标解耦，以及 2DOF 系统在自由、简谐和一般激励下的响应。

## 1. 从 SDOF 到 2DOF

2DOF 系统需要两个相互独立的广义坐标，例如

$$
\mathbf x(t)=
\begin{bmatrix}
x_1(t)\\x_2(t)
\end{bmatrix}.
$$

线性 2DOF 系统的一般方程为

$$
\boxed{
\mathbf M\ddot{\mathbf x}
+\mathbf C\dot{\mathbf x}
+\mathbf K\mathbf x
=\mathbf F(t)}
$$

其中：

- $\mathbf M$ 为质量矩阵；
- $\mathbf C$ 为阻尼矩阵；
- $\mathbf K$ 为刚度矩阵；
- $\mathbf F(t)$ 为广义外力向量。

与 SDOF 相比，2DOF 的关键变化是：

1. 方程是相互耦合的矩阵微分方程；
2. 系统有两个固有频率和两个对应振型；
3. 一般响应是两个模态响应的叠加；
4. 需要使用矩阵代数和广义特征值问题；
5. 模态坐标可以把耦合方程转换为相互独立的 SDOF 方程。

## 2. Lagrange 方程建模

### 2.1 为什么使用能量法

对多自由度系统，直接使用 Newton 法通常需要：

- 为每个物体画自由体图；
- 引入并消去绳张力、铰链力等内部约束力；
- 同时处理多条标量方程。

Lagrange 法只需选择最少数量的独立广义坐标，并计算动能、势能、耗散函数和广义外力，尤其适合摆、刚体和复杂约束系统。

### 2.2 Lagrange 方程

定义 Lagrange 函数

$$
L=T-V,
$$

其中 $T$ 为动能，$V$ 为势能。对广义坐标 $q_j$：

$$
\boxed{
\frac{\mathrm d}{\mathrm dt}
\left(\frac{\partial L}{\partial\dot q_j}\right)
-\frac{\partial L}{\partial q_j}
=Q_{j,\mathrm{nc}}}
$$

若含黏性阻尼，定义 Rayleigh 耗散函数

$$
\mathcal D=\frac12\sum_i\sum_j c_{ij}\dot q_i\dot q_j,
$$

则

$$
\boxed{
\frac{\mathrm d}{\mathrm dt}
\left(\frac{\partial L}{\partial\dot q_j}\right)
-\frac{\partial L}{\partial q_j}
+\frac{\partial\mathcal D}{\partial\dot q_j}
=Q_{j,\mathrm{nc}}}.
$$

### 2.3 广义力

广义力通过虚功确定：

$$
\delta W_{\mathrm{nc}}
=\sum_j Q_{j,\mathrm{nc}}\,\delta q_j.
$$

若外力 $\mathbf F$ 作用点的位置为 $\mathbf r(q_1,q_2)$，则

$$
Q_j=\mathbf F\cdot\frac{\partial\mathbf r}{\partial q_j}.
$$

例如，水平力 $F$ 作用在长度为 $\ell$ 的摆端，以 $\theta$ 为坐标：

$$
Q_\theta=F\ell\cos\theta.
$$

它在物理上就是外力关于摆轴的力矩。

### 2.4 线性化

许多摆和刚体系统首先得到非线性方程。小振幅时使用

$$
\sin\theta\simeq\theta,\qquad
\cos\theta\simeq1,
$$

并忽略 $\theta^2$、$\dot\theta^2\theta$ 等高阶项，最终得到常系数矩阵方程。

**重要顺序：** 先建立完整的运动学、动能和势能，再在线性方程阶段作小角度近似。过早近似容易漏掉惯性耦合项。

## 3. 质量、阻尼和刚度矩阵的装配

### 3.1 两质量弹簧阻尼系统

若 $m_1,m_2$ 分别接地，并由中间弹簧 $k_2$ 和阻尼器 $c_2$ 耦合，典型矩阵为

$$
\mathbf M=
\begin{bmatrix}
m_1&0\\
0&m_2
\end{bmatrix},
$$

$$
\mathbf C=
\begin{bmatrix}
c_1+c_2&-c_2\\
-c_2&c_2+c_3
\end{bmatrix},
\qquad
\mathbf K=
\begin{bmatrix}
k_1+k_2&-k_2\\
-k_2&k_2+k_3
\end{bmatrix}.
$$

耦合弹簧的势能为

$$
V_c=\frac12k_c(x_2-x_1)^2.
$$

展开后可立即看出：

- 两个对角元各增加 $k_c$；
- 两个非对角元均为 $-k_c$。

耦合阻尼器同理。因此，保守机械系统用一致坐标建立的 $\mathbf M$、$\mathbf K$ 通常应为对称矩阵。

### 3.2 两种耦合

- **刚度耦合：** $\mathbf K$ 的非对角元不为零；
- **惯性耦合：** $\mathbf M$ 的非对角元不为零，例如双摆、绳－杆系统；
- 实际系统可以同时具有刚度、惯性和阻尼耦合。

矩阵是否耦合取决于所选坐标。换一组坐标可能改变耦合形式，但不会改变系统的固有频率。

### 3.3 基座输入

当某个弹簧和阻尼器连接到运动基座 $y(t)$ 时，相对变形为 $x_1-y$，相对速度为 $\dot x_1-\dot y$。展开后，基座运动移到方程右侧：

$$
\mathbf M\ddot{\mathbf x}
+\mathbf C\dot{\mathbf x}
+\mathbf K\mathbf x
=
\begin{bmatrix}
c_1\dot y+k_1y\\0
\end{bmatrix}
$$

（具体位置取决于基座连接在哪个自由度）。不能把基座位移直接当作普通外力。

## 4. 无阻尼自由振动与特征值问题

Lecture 04 的模态分析核心针对

$$
\boxed{\mathbf M\ddot{\mathbf x}+\mathbf K\mathbf x=0}
$$

其中 $\mathbf M,\mathbf K$ 为实对称矩阵；对稳定且无刚体模态的系统，它们为正定矩阵。

### 4.1 分离变量

设系统作同步简谐运动：

$$
\mathbf x(t)=\mathbf u\,e^{i\omega t}.
$$

代入得

$$
(\mathbf K-\omega^2\mathbf M)\mathbf u=0,
$$

即广义特征值问题

$$
\boxed{
\mathbf K\mathbf u
=\lambda\mathbf M\mathbf u,
\qquad \lambda=\omega^2}.
$$

要使 $\mathbf u\ne0$，必须满足

$$
\boxed{\det(\mathbf K-\omega^2\mathbf M)=0}.
$$

该式称为频率方程或特征方程。2DOF 系统通常得到两个特征值

$$
\lambda_1=\omega_1^2,\qquad
\lambda_2=\omega_2^2,
$$

以及两个对应振型 $\mathbf u_1,\mathbf u_2$。

### 4.2 一般 2×2 频率方程

令

$$
\mathbf M=
\begin{bmatrix}
m_{11}&m_{12}\\
m_{12}&m_{22}
\end{bmatrix},
\qquad
\mathbf K=
\begin{bmatrix}
k_{11}&k_{12}\\
k_{12}&k_{22}
\end{bmatrix}.
$$

以 $\lambda=\omega^2$ 为未知量：

$$
\boxed{
(m_{11}m_{22}-m_{12}^2)\lambda^2
-\left(k_{11}m_{22}+k_{22}m_{11}-2k_{12}m_{12}\right)\lambda
+(k_{11}k_{22}-k_{12}^2)=0}.
$$

解出 $\lambda_1,\lambda_2$ 后，取正平方根得到 $\omega_1,\omega_2$。

### 4.3 Rayleigh 商与特征值性质

由 $\mathbf K\mathbf u=\lambda\mathbf M\mathbf u$：

$$
\boxed{
\lambda=
\frac{\mathbf u^{\mathsf T}\mathbf K\mathbf u}
{\mathbf u^{\mathsf T}\mathbf M\mathbf u}}.
$$

若 $\mathbf M,\mathbf K$ 实对称且正定，则：

- 特征值为实数且为正；
- 固有频率为实数；
- 振型可选为实向量；
- 2DOF 系统有两个独立振型。

若 $\mathbf K$ 仅为半正定，可能出现 $\omega=0$ 的刚体模态，这不代表计算错误。

## 5. 振型及其物理含义

### 5.1 振型只确定相对幅值

对某个 $\omega_j$，代回

$$
(\mathbf K-\omega_j^2\mathbf M)\mathbf u_j=0
$$

求得

$$
\mathbf u_j=
\begin{bmatrix}
u_{1j}\\u_{2j}
\end{bmatrix}.
$$

振型的核心信息是幅值比

$$
\frac{u_{2j}}{u_{1j}}.
$$

若 $\mathbf u_j$ 是振型，则任意非零倍数 $a\mathbf u_j$ 也是同一振型。因此，振型的绝对数值没有唯一性，必须说明采用了何种归一化。

### 5.2 同相、反相和节点

- 两个分量同号：两个自由度同相运动；
- 两个分量异号：两个自由度反相运动；
- 振型中位移始终为零的位置称为节点；
- 低阶模态通常变形较平缓、节点较少；
- 高阶模态通常相对运动更强、节点更多。

对两个相同质量连接在对称拉紧弦上的例子：

$$
\mathbf u_1=
\begin{bmatrix}1\\1\end{bmatrix},
\qquad
\mathbf u_2=
\begin{bmatrix}1\\-1\end{bmatrix}.
$$

第一模态同相且两质量之间无节点；第二模态反相，在两质量之间出现一个节点。

### 5.3 单模态运动与一般运动

若初始条件只激发第 $j$ 个模态：

$$
\mathbf x(t)=q_j(t)\mathbf u_j,
$$

则所有物理坐标：

- 以同一个 $\omega_j$ 振动；
- 保持固定的幅值比；
- 同时经过平衡位置并同时到达极值。

一般初始条件会同时激发两个模态，系统瞬时形状随时间变化。

## 6. 模态正交性和归一化

对不同特征值 $\lambda_i\ne\lambda_j$：

$$
\boxed{
\mathbf u_i^{\mathsf T}\mathbf M\mathbf u_j=0},
$$

$$
\boxed{
\mathbf u_i^{\mathsf T}\mathbf K\mathbf u_j=0}.
$$

这不是普通欧氏正交，而是关于质量矩阵和刚度矩阵的加权正交。

### 6.1 模态质量和模态刚度

未归一化振型的模态质量、模态刚度为

$$
m_j'=\mathbf u_j^{\mathsf T}\mathbf M\mathbf u_j,
$$

$$
k_j'=\mathbf u_j^{\mathsf T}\mathbf K\mathbf u_j
=m_j'\omega_j^2.
$$

### 6.2 质量归一化

令

$$
\boldsymbol\phi_j=
\frac{\mathbf u_j}
{\sqrt{\mathbf u_j^{\mathsf T}\mathbf M\mathbf u_j}},
$$

并组成模态矩阵

$$
\mathbf\Phi=
\begin{bmatrix}
\boldsymbol\phi_1&\boldsymbol\phi_2
\end{bmatrix}.
$$

则

$$
\boxed{
\mathbf\Phi^{\mathsf T}\mathbf M\mathbf\Phi=\mathbf I},
$$

$$
\boxed{
\mathbf\Phi^{\mathsf T}\mathbf K\mathbf\Phi
=
\mathbf\Omega^2
=
\begin{bmatrix}
\omega_1^2&0\\
0&\omega_2^2
\end{bmatrix}}.
$$

数值软件返回的振型不一定已按质量归一化，使用前应检查。

## 7. 模态坐标与方程解耦

作坐标变换

$$
\boxed{\mathbf x=\mathbf\Phi\mathbf q},
$$

其中

$$
\mathbf q=
\begin{bmatrix}
q_1\\q_2
\end{bmatrix}
$$

为模态坐标。代入自由振动方程，并左乘 $\mathbf\Phi^{\mathsf T}$：

$$
\ddot{\mathbf q}+\mathbf\Omega^2\mathbf q=0.
$$

即

$$
\boxed{
\ddot q_1+\omega_1^2q_1=0,\qquad
\ddot q_2+\omega_2^2q_2=0}.
$$

原来耦合的两个方程被转换成两个独立的 SDOF 方程。这是模态分析最重要的结果。

### 7.1 由初始条件求自由响应

给定

$$
\mathbf x(0)=\mathbf x_0,\qquad
\dot{\mathbf x}(0)=\mathbf v_0,
$$

质量归一化后：

$$
\boxed{
\mathbf q(0)=\mathbf\Phi^{\mathsf T}\mathbf M\mathbf x_0},
$$

$$
\boxed{
\dot{\mathbf q}(0)
=\mathbf\Phi^{\mathsf T}\mathbf M\mathbf v_0}.
$$

每个模态的响应为

$$
q_j(t)=q_j(0)\cos\omega_jt
+\frac{\dot q_j(0)}{\omega_j}\sin\omega_jt.
$$

最后变回物理坐标：

$$
\boxed{
\mathbf x(t)=
\sum_{j=1}^{2}
\boldsymbol\phi_j
\left[
q_j(0)\cos\omega_jt
+\frac{\dot q_j(0)}{\omega_j}\sin\omega_jt
\right]}.
$$

若振型未归一化，则

$$
q_j(0)=
\frac{\mathbf u_j^{\mathsf T}\mathbf M\mathbf x_0}
{\mathbf u_j^{\mathsf T}\mathbf M\mathbf u_j},
\qquad
\dot q_j(0)=
\frac{\mathbf u_j^{\mathsf T}\mathbf M\mathbf v_0}
{\mathbf u_j^{\mathsf T}\mathbf M\mathbf u_j}.
$$

## 8. 弱耦合系统与拍振

两个近似相同的振子由较弱的弹簧连接时：

$$
\omega_1\simeq\omega_2.
$$

对称系统常有

$$
\mathbf u_1=
\begin{bmatrix}1\\1\end{bmatrix},
\qquad
\mathbf u_2=
\begin{bmatrix}1\\-1\end{bmatrix}.
$$

若初始时只使第一个振子偏离平衡位置，响应可写成类似

$$
\theta_1(t)=
\theta_0
\cos\left(\frac{\omega_2-\omega_1}{2}t\right)
\cos\left(\frac{\omega_2+\omega_1}{2}t\right),
$$

$$
\theta_2(t)=
\theta_0
\sin\left(\frac{\omega_2-\omega_1}{2}t\right)
\sin\left(\frac{\omega_2+\omega_1}{2}t\right).
$$

其中：

- $(\omega_1+\omega_2)/2$ 决定快速振动；
- $|\omega_2-\omega_1|/2$ 决定慢变化包络；
- 能量在两个振子之间周期性交换；
- 一个振子的振幅最大时，另一个可能接近零。

按振幅绝对值定义，拍振周期约为

$$
T_{\mathrm{beat}}=
\frac{2\pi}{|\omega_2-\omega_1|}.
$$

两频率越接近，拍振越慢、能量交换周期越长。

## 9. 2DOF 简谐强迫响应

考虑

$$
\mathbf M\ddot{\mathbf x}
+\mathbf C\dot{\mathbf x}
+\mathbf K\mathbf x
=\mathbf F_0e^{i\omega t}.
$$

设稳态响应为

$$
\mathbf x(t)=\mathbf X(\omega)e^{i\omega t}.
$$

代入得

$$
\boxed{
\mathbf Z(i\omega)\mathbf X=\mathbf F_0},
$$

其中动态刚度或机械阻抗矩阵为

$$
\boxed{
\mathbf Z(i\omega)
=-\omega^2\mathbf M+i\omega\mathbf C+\mathbf K}.
$$

因此

$$
\boxed{
\mathbf X(\omega)=\mathbf Z^{-1}(i\omega)\mathbf F_0}.
$$

无阻尼时：

$$
\mathbf Z=\mathbf K-\omega^2\mathbf M.
$$

当激励频率接近某个固有频率时，$\det\mathbf Z$ 接近零，响应出现共振峰。不同测点还可能因分子为零而出现**反共振（antiresonance）**，即某一坐标响应为零。

直接求逆适用于小型系统；自由度较多时，模态叠加通常更清晰、更高效。

## 10. 动力吸振器

动力吸振器在主系统上附加一个质量－弹簧子系统：

- 主系统：$m_1,k_1$；
- 吸振器：$m_2,k_2$；
- 外力作用在主质量 $m_1$ 上。

运动方程为

$$
m_1\ddot x_1+(k_1+k_2)x_1-k_2x_2
=F_0\sin\omega t,
$$

$$
m_2\ddot x_2-k_2x_1+k_2x_2=0.
$$

定义吸振器固有频率

$$
\omega_a=\sqrt{\frac{k_2}{m_2}}.
$$

理想无阻尼情况下，若调谐为

$$
\boxed{\omega_a=\omega},
$$

则主质量的稳态响应可达到

$$
\boxed{X_1=0}.
$$

此时吸振器弹簧产生的反向力恰好抵消外部简谐力。物理上应注意：

- 原主系统的一个共振峰被分裂为两个新的共振峰；
- 调谐点出现反共振凹口；
- 理想吸振只在调谐频率附近有效；
- 吸振器质量会产生较大运动，实际设计需考虑阻尼、行程和参数偏差。

## 11. 2DOF 非周期激励的模态响应

对无阻尼系统

$$
\mathbf M\ddot{\mathbf x}
+\mathbf K\mathbf x
=\mathbf F(t),
$$

使用未归一化模态矩阵 $\mathbf U=[\mathbf u_1,\mathbf u_2]$，令

$$
\mathbf x=\mathbf U\boldsymbol\eta.
$$

第 $j$ 个模态方程为

$$
\boxed{
m_j'\ddot\eta_j
+m_j'\omega_j^2\eta_j
=N_j(t)},
$$

其中

$$
m_j'=\mathbf u_j^{\mathsf T}\mathbf M\mathbf u_j,
\qquad
N_j(t)=\mathbf u_j^{\mathsf T}\mathbf F(t).
$$

$N_j(t)$ 称为模态力。零初始条件下：

$$
\boxed{
\eta_j(t)=
\frac1{m_j'\omega_j}
\int_0^t
N_j(\tau)
\sin[\omega_j(t-\tau)]\,\mathrm d\tau}.
$$

最终物理响应为

$$
\boxed{
\mathbf x(t)=
\sum_{j=1}^{2}\mathbf u_j\eta_j(t)}.
$$

质量归一化后 $m_j'=1$，公式进一步简化。若载荷只有离散采样值，可把卷积积分改成卷积求和。

这一过程可以理解为：

> 物理外力 $\mathbf F(t)$ → 投影为各阶模态力 $N_j(t)$ → 分别求两个 SDOF 卷积响应 → 按振型叠加回物理坐标。

## 12. 阻尼系统的模态分析边界

对

$$
\mathbf M\ddot{\mathbf x}
+\mathbf C\dot{\mathbf x}
+\mathbf K\mathbf x
=\mathbf F(t),
$$

无阻尼振型一定能对角化 $\mathbf M$ 和 $\mathbf K$，但一般**不能保证**

$$
\mathbf\Phi^{\mathsf T}\mathbf C\mathbf\Phi
$$

也是对角矩阵。

因此：

- 无阻尼系统可直接用实模态完全解耦；
- 比例阻尼或经典阻尼系统也可用相同实模态解耦；
- 一般非比例阻尼系统需要更完整的复模态或状态空间方法。

本讲重点是无阻尼 2DOF 的实模态分析，复杂阻尼问题留待 MDOF 内容。

## 13. MATLAB 求解思路

对已建立的 $\mathbf M,\mathbf K$：

1. 使用广义特征值求解得到 $\mathbf K\mathbf U=\mathbf M\mathbf U\mathbf\Lambda$；
2. $\mathbf\Lambda$ 的对角元是 $\omega_j^2$；
3. 对特征值排序时，必须同步调整 $\mathbf U$ 的列；
4. 对每列振型作质量归一化；
5. 检查

   $$
   \mathbf\Phi^{\mathsf T}\mathbf M\mathbf\Phi\simeq\mathbf I,
   \qquad
   \mathbf\Phi^{\mathsf T}\mathbf K\mathbf\Phi\simeq\mathbf\Omega^2.
   $$

6. 将初始条件或载荷投影到模态坐标，分别计算各阶响应；
7. 用 $\mathbf x=\mathbf\Phi\mathbf q$ 恢复物理响应。

数值上还应注意量纲差异过大造成的条件数问题；必要时先作无量纲化或尺度缩放。

## 14. 典型建模例题带来的通用结论

### 14.1 双摆和绳－杆系统

- 动能中出现 $\dot q_1\dot q_2$ 交叉项，说明存在惯性耦合；
- 用 Lagrange 法通常比消去张力和约束力更直接；
- 小角度线性化后应得到对称质量矩阵和刚度矩阵；
- 选择不同广义坐标会改变矩阵形式，但固有频率不变。

### 14.2 半车与两质量基座激励

- 每个弹簧力取决于两端的相对位移；
- 每个阻尼力取决于两端的相对速度；
- 基座项应移到右侧成为等效输入；
- 装配矩阵时可通过对角元之和、非对角元符号和矩阵对称性检查结果。

### 14.3 对称系统

对称结构往往可以先根据物理对称性猜出

$$
\begin{bmatrix}1\\1\end{bmatrix},
\qquad
\begin{bmatrix}1\\-1\end{bmatrix}
$$

两类振型，再代入方程求频率。这样比直接展开行列式更快，也更容易解释物理意义。

## 15. 2DOF 解题流程

1. 选择两个独立广义坐标并明确正方向。
2. 用 Newton 法或 Lagrange 法建立两条运动方程。
3. 写成 $\mathbf M\ddot{\mathbf x}+\mathbf C\dot{\mathbf x}+\mathbf K\mathbf x=\mathbf F$。
4. 检查 $\mathbf M,\mathbf K$ 的量纲、对称性和正定性。
5. 求自由振动时令 $\mathbf C=0,\mathbf F=0$。
6. 建立 $\det(\mathbf K-\omega^2\mathbf M)=0$，先求 $\omega_1,\omega_2$。
7. 分别代回求 $\mathbf u_1,\mathbf u_2$ 的分量比。
8. 按题目需要作质量归一化。
9. 用模态正交性把初始条件或载荷投影到模态空间。
10. 分别解两个 SDOF 模态方程，再叠加回物理坐标。
11. 用同相/反相、节点、拍振、共振和反共振解释结果。

## 16. 常见错误

- 把特征值 $\lambda=\omega^2$ 直接当作 $\omega$；
- 求出固有频率后没有继续求振型；
- 把振型的绝对大小当成唯一结果，而忽略其任意比例性；
- 用普通点积判断模态正交，忘记质量矩阵权重；
- 数值软件返回振型后默认其已质量归一化；
- 初值转换时直接使用 $\mathbf q_0=\mathbf\Phi^{\mathsf T}\mathbf x_0$，漏掉 $\mathbf M$；
- 只对角化 $\mathbf M,\mathbf K$，却默认任意 $\mathbf C$ 也会被对角化；
- 耦合弹簧的非对角刚度写成正号；
- 基座输入直接写进外力向量，漏掉 $k y+c\dot y$；
- 在非线性运动学关系中过早使用小角度近似；
- 只算两个频率，不检查振型是否符合对称性和物理直觉。

## 17. 最小公式速查

运动方程：

$$
\boxed{
\mathbf M\ddot{\mathbf x}
+\mathbf C\dot{\mathbf x}
+\mathbf K\mathbf x
=\mathbf F(t)}
$$

自由振动特征值问题：

$$
\boxed{
\mathbf K\mathbf u_j
=\omega_j^2\mathbf M\mathbf u_j},
\qquad
\boxed{
\det(\mathbf K-\omega^2\mathbf M)=0}.
$$

正交性：

$$
\boxed{
\mathbf u_i^{\mathsf T}\mathbf M\mathbf u_j=0,\quad
\mathbf u_i^{\mathsf T}\mathbf K\mathbf u_j=0
\quad(i\ne j)}.
$$

质量归一化：

$$
\boxed{
\mathbf\Phi^{\mathsf T}\mathbf M\mathbf\Phi=\mathbf I,\qquad
\mathbf\Phi^{\mathsf T}\mathbf K\mathbf\Phi=\mathbf\Omega^2}.
$$

模态变换：

$$
\boxed{
\mathbf x=\mathbf\Phi\mathbf q,\qquad
\ddot{\mathbf q}+\mathbf\Omega^2\mathbf q=0}.
$$

初始条件投影：

$$
\boxed{
\mathbf q_0=\mathbf\Phi^{\mathsf T}\mathbf M\mathbf x_0,\qquad
\dot{\mathbf q}_0=\mathbf\Phi^{\mathsf T}\mathbf M\mathbf v_0}.
$$

简谐稳态响应：

$$
\boxed{
\mathbf X(\omega)=
[-\omega^2\mathbf M+i\omega\mathbf C+\mathbf K]^{-1}
\mathbf F_0}.
$$

零初值非周期模态响应：

$$
\boxed{
\eta_j(t)=
\frac1{m_j'\omega_j}
\int_0^t
\mathbf u_j^{\mathsf T}\mathbf F(\tau)
\sin[\omega_j(t-\tau)]\,\mathrm d\tau}.
$$

本讲最重要的主线是：

> 建立矩阵方程 → 解广义特征值问题 → 得到固有频率与振型 → 利用正交性转到模态坐标 → 把耦合的 2DOF 系统化成两个独立 SDOF 系统 → 求响应并叠加回物理坐标。
