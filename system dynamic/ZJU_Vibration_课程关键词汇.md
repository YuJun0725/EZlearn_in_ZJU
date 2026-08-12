# 《系统动力学（振动）》课程关键词汇

本表根据以下两份课程讲义整理：

- `ZJU_Vibration_Lecture01_Introduction.pdf`：振动概论与背景
- `ZJU_Vibration_Lecture01_SDOF_FreeVib_2026.pdf`：单自由度系统自由振动
- `ZJU_Vibration_Lecture02_SDOF_ForcedVib_Harmonic_2026.pdf`：单自由度系统强迫振动与简谐响应

## 1. 系统动力学与建模

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| dynamic system | 动力系统 | 状态随时间变化、需要用运动方程描述的系统 |
| system dynamics | 系统动力学 | 研究动力系统建模、响应和稳定性的学科 |
| modeling | 建模 | 将实际机械或结构系统理想化为可分析的模型 |
| analysis | 分析 | 求解并解释系统的运动、响应和振动特性 |
| physical model | 物理模型 | 对实际结构、质量、弹簧、阻尼等的理想化表示 |
| mathematical model | 数学模型 | 用方程、矩阵或状态空间形式描述物理模型 |
| governing equation of motion | 控制运动方程 | 描述系统运动规律的微分方程 |
| degree of freedom (DOF) | 自由度 | 完整描述系统运动所需的最少独立坐标数 |
| single-degree-of-freedom (SDOF) system | 单自由度系统 | 只需要一个独立坐标描述的振动系统 |
| two-degree-of-freedom (2DOF) system | 二自由度系统 | 需要两个独立坐标描述的系统 |
| multi-degree-of-freedom (MDOF) system | 多自由度系统 | 具有多个集中质量和独立运动坐标的系统 |
| distributed-parameter system | 分布参数系统 | 质量和变形连续分布的系统，如梁、板和连续体 |
| lumped-parameter system | 集中参数系统 | 用离散质量、刚度和阻尼元件近似实际结构 |
| physical significance | 物理意义 | 数学结果对应的实际工程含义 |
| generalized coordinate | 广义坐标 | 描述系统构型并用于建立方程的独立坐标 |
| coordinate system | 坐标系 | 确定位移、转角和运动正方向的参考系 |
| equilibrium position | 平衡位置 | 各作用力或力矩平衡时的位置 |
| Newton's laws | 牛顿定律 | 通过力和加速度推导运动方程的方法 |
| Lagrange's equations | 拉格朗日方程 | 基于能量和广义坐标建立运动方程的方法 |
| constitutive relation | 本构关系 | 描述材料或元件力学量之间关系的方程 |
| linear vibration | 线性振动 | 在小振幅假设下，方程和响应满足线性关系 |
| nonlinear vibration | 非线性振动 | 含非线性力、刚度或边界条件的振动 |
| small-amplitude assumption | 小振幅假设 | 将非线性几何或力学关系线性化的常用假设 |

## 2. 振动基础概念

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| vibration | 振动 | 系统围绕平衡状态的往复或周期性运动 |
| oscillation | 振荡 | 强调重复性往复运动的振动过程 |
| amplitude | 幅值 | 位移、速度或加速度响应的最大量级 |
| frequency | 频率 | 单位时间内的周期数，单位通常为 Hz |
| angular frequency | 圆频率 | 以 rad/s 表示的频率，通常记为 $\omega$ |
| natural frequency | 固有频率 | 系统在自由振动时由自身参数决定的频率 |
| natural angular frequency | 固有圆频率 | 通常记为 $\omega_n$，无阻尼 SDOF 中 $\omega_n=\sqrt{k/m}$ |
| natural period | 固有周期 | 完成一次自由振动所需的时间，记为 $T_n$ |
| phase angle | 相位角 | 描述响应相对于参考正弦或余弦信号的相位位置 |
| phase shift | 相位差 | 激励与响应，或位移与速度之间的相位偏移 |
| simple harmonic motion | 简谐运动 | 由正弦或余弦函数描述的理想周期运动 |
| free vibration | 自由振动 | 由初始扰动引起、没有持续外力的振动 |
| forced vibration | 强迫振动 | 由持续外部激励引起的振动 |
| external disturbance | 外部扰动 | 使系统偏离平衡状态的外界作用 |
| initial disturbance | 初始扰动 | 初始位移、初始速度或冲击等起始作用 |
| initial condition | 初始条件 | 确定微分方程唯一响应所需的初始位移和速度 |
| transient response | 瞬态响应 | 随时间衰减或变化的初始响应部分 |
| steady-state response | 稳态响应 | 激励持续后保留下来的长期响应部分 |
| harmonic excitation | 简谐激励 | 按正弦或余弦规律变化的外部激励 |
| periodic excitation | 周期激励 | 以固定周期重复的激励 |
| non-periodic excitation | 非周期激励 | 不按固定周期重复的激励 |
| impulse | 冲击 | 作用时间很短但可能具有明显动量输入的激励 |
| deterministic excitation | 确定性激励 | 时间历程可用明确函数描述的激励 |
| random excitation | 随机激励 | 需要概率统计特性描述的激励 |
| resonance | 共振 | 激励频率接近系统固有频率时响应显著放大的现象 |
| frequency-domain analysis | 频域分析 | 在频率域研究系统幅值、相位和响应特性 |
| frequency response | 频率响应 | 响应幅值和相位随激励频率变化的关系 |
| stability | 稳定性 | 扰动后响应是否保持有界并趋于平衡的性质 |
| asymptotically stable | 渐近稳定 | 响应随时间趋于平衡状态 |

## 3. 振动系统的基本元件

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| inertia | 惯性 | 物体抵抗速度变化的性质，集中体现为质量或转动惯量 |
| mass | 质量 | 平动系统的惯性参数，通常记为 $m$ |
| moment of inertia | 转动惯量 | 转动系统的惯性参数，常记为 $I$ 或 $J$ |
| stiffness | 刚度 | 元件抵抗变形并产生回复力的能力，通常记为 $k$ |
| structural flexibility | 结构柔度 | 结构发生变形的能力，与刚度相对应 |
| spring | 弹簧 | 提供与位移相关的回复力的元件 |
| equivalent stiffness | 等效刚度 | 将多个弹簧或结构部件等效为单个刚度 |
| restoring force | 回复力 | 将系统拉回平衡位置的力 |
| damping | 阻尼 | 消耗机械振动能量的机制 |
| energy dissipation | 能量耗散 | 机械能转化为热能等其他形式能量的过程 |
| damper | 阻尼器 | 提供阻尼力、抑制响应的元件 |
| viscous damper | 黏性阻尼器 | 阻尼力与相对速度成正比的阻尼元件 |
| damping coefficient | 阻尼系数 | 黏性阻尼大小的参数，通常记为 $c$ |
| dashpot | 黏性阻尼器 | viscous damper 的常用机械模型名称 |
| shock absorber | 减振器 | 车辆悬架中用于耗散振动能量的阻尼元件 |
| coil spring | 螺旋弹簧 | 汽车悬架中提供刚度的弹簧元件 |
| series connection | 串联 | 弹簧或元件首尾连接，等效柔度相加 |
| parallel connection | 并联 | 元件承受相同位移，等效刚度相加 |

## 4. SDOF 自由振动与阻尼

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| undamped system | 无阻尼系统 | $c=0$，机械能守恒的理想系统 |
| damped system | 有阻尼系统 | 存在能量耗散，响应随时间衰减的系统 |
| damping ratio | 阻尼比 | 无量纲参数，通常记为 $\zeta=c/(2\sqrt{km})$ |
| damped natural frequency | 阻尼固有频率 | 欠阻尼系统的振荡频率，通常记为 $\omega_d$ |
| characteristic equation | 特征方程 | 由运动方程得到、用于求特征根的代数方程 |
| characteristic root | 特征根 | 特征方程的根，决定响应的指数形式和稳定性 |
| eigenvalue | 特征值 | 状态空间或模态分析中与特征根相关的量 |
| underdamped | 欠阻尼 | $\zeta<1$，响应具有衰减振荡 |
| critically damped | 临界阻尼 | $\zeta=1$，无振荡且通常具有最快的非振荡响应 |
| overdamped | 过阻尼 | $\zeta>1$，无振荡但响应通常慢于临界阻尼 |
| oscillatory response | 振荡响应 | 包含正弦或余弦项的响应 |
| decaying exponential | 衰减指数 | 形如 $e^{-at}$ 的响应项 |
| response envelope | 响应包络 | 表示振荡幅值随时间变化的外包络 |
| time constant | 时间常数 | 衡量指数响应衰减速度的时间尺度 |
| phase relation | 相位关系 | 位移、速度、加速度或激励之间的相位联系 |
| kinetic energy | 动能 | 平动或转动运动产生的能量 |
| potential energy | 势能 | 弹簧、重力等保守力储存的能量 |
| mechanical energy | 机械能 | 动能与势能之和 |
| conservation of energy | 能量守恒 | 无阻尼系统分析中的基本方法 |
| energy functional | 能量泛函 | 用于优化或评价响应能量的函数，如作用量 |

## 5. 阻尼测量与响应识别

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| damping measurement | 阻尼测量 | 通过动态试验确定阻尼系数或阻尼比 |
| static test | 静态试验 | 讲义中用于测量刚度的试验方式 |
| dynamic test | 动态试验 | 讲义中用于测量阻尼的试验方式 |
| logarithmic decrement | 对数减量 | 从欠阻尼自由响应相邻峰值衰减识别阻尼比的方法 |
| per-cycle logarithmic decrement | 每周期对数减量 | 跨越一个或多个周期的峰值比取对数 |
| per-radian logarithmic decrement | 每弧度对数减量 | 将每周期对数减量除以 $2\pi n$ 得到的量 |
| peak response | 峰值响应 | 响应曲线上的局部最大值，常用于阻尼识别 |
| half-power method | 半功率法 | 根据谐波强迫响应的带宽估计阻尼的方法 |
| bandwidth | 带宽 | 描述频率响应达到特定幅值范围的频率区间 |
| transfer function | 传递函数 | 频域中输入与输出之比的系统描述 |
| convolution integral | 卷积积分 | 求解任意激励下线性系统响应的方法 |
| Laplace transform | 拉普拉斯变换 | 将时域微分方程转换为代数方程的变换方法 |

## 6. 数值计算与 MATLAB

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| analytical solution | 解析解 | 通过符号推导得到的闭式或明确表达式 |
| semi-analytical solution | 半解析解 | 结合解析推导和数值计算得到的解 |
| numerical solution | 数值解 | 通过离散算法或数值积分得到的近似解 |
| numerical simulation | 数值仿真 | 用计算机模拟系统随时间的响应 |
| state-space formulation | 状态空间表达 | 将高阶方程改写为一阶状态方程组 |
| state vector | 状态向量 | 由位移、速度等状态变量组成的向量 |
| coefficient matrix | 系数矩阵 | 状态方程中描述系统参数的矩阵 |
| Euler method | 欧拉法 | 基于当前斜率推进下一时间步的数值方法 |
| Runge–Kutta method | 龙格–库塔法 | 精度较高的常微分方程数值积分方法 |
| adaptive time step | 自适应时间步长 | 根据局部响应变化自动调整积分步长 |
| ordinary differential equation (ODE) | 常微分方程 | 以时间及其导数描述系统运动的方程 |
| ODE solver | 常微分方程求解器 | 用于数值积分 ODE 的程序工具 |
| `ode23` | MATLAB 常微分方程求解器 | 基于低阶龙格–库塔方法的数值积分函数 |
| `ode45` | MATLAB 常微分方程求解器 | 常用的自适应龙格–库塔数值积分函数 |
| `fminsearch` | MATLAB 无约束优化函数 | 讲义中用于寻找响应最大值 |
| `fzero` | MATLAB 求根函数 | 讲义中用于寻找达到指定响应的时间 |
| time history | 时间历程 | 位移、速度或能量随时间变化的曲线 |
| normalized response | 归一化响应 | 例如用 $x/x_0$ 表示相对于初始位移的响应 |
| normalized energy | 归一化能量 | 用当前机械能与初始能量之比表示能量变化 |
| plot | 绘图 | 将计算得到的响应数据可视化 |
| legend | 图例 | 标识曲线对应的参数或工况 |

## 7. 工程应用词汇

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| vibration isolation | 振动隔离 | 减少振动从激励源向设备或结构传递的技术 |
| vibration control | 振动控制 | 通过被动、半主动或主动方法降低振动 |
| structural vibration control | 结构振动控制 | 针对桥梁、建筑和机械结构的振动抑制 |
| active vibration control | 主动振动控制 | 使用传感器、执行器和控制算法主动施加控制力 |
| passive control | 被动控制 | 使用弹簧、阻尼器、隔振器等无需外部能量的控制方式 |
| tuned mass damper (TMD) | 调谐质量阻尼器 | 通过调节附加质量的固有频率来吸收结构振动 |
| actuator | 执行器 | 将控制信号转化为力、位移或其他物理作用的装置 |
| smart material | 智能材料 | 可感知或响应外部刺激、用于结构控制的材料 |
| energy harvesting | 能量采集 | 将环境振动转换为可利用电能的技术 |
| accelerometer | 加速度计 | 测量系统加速度的传感器 |
| ultrasonic vibration welding | 超声波振动焊接 | 利用高频振动实现材料连接的工艺 |
| sonotrode | 超声焊头 | 将超声振动传递到焊接区域的工具 |
| unbalanced load | 不平衡荷载 | 由转动部件质量分布不均引起的周期激励 |
| wind loading | 风荷载 | 风作用于建筑或结构形成的外部激励 |
| earthquake excitation | 地震激励 | 地面运动对结构产生的动态输入 |
| bridge oscillation | 桥梁振动 | 交通、风或行人荷载引起的桥梁响应 |
| brake squeal | 制动尖叫 | 制动系统摩擦诱发的高频振动与噪声 |
| structural failure | 结构失效 | 振动过大、疲劳或灾害导致的功能或承载能力丧失 |
| damage identification | 损伤识别 | 根据响应或模态特性判断结构参数变化和损伤位置 |
| parameter identification | 参数识别 | 根据实验或响应数据反推质量、刚度、阻尼等参数 |

## 8. 常用符号与缩写

| 符号或缩写 | 含义 | 常见单位或说明 |
| --- | --- | --- |
| $m$ | 质量 | kg |
| $k$ | 刚度 | N/m |
| $c$ | 黏性阻尼系数 | N·s/m |
| $x(t)$ | 位移响应 | m；也可表示相对于平衡位置的坐标 |
| $\dot{x}(t)$ | 速度响应 | m/s |
| $\ddot{x}(t)$ | 加速度响应 | m/s² |
| $x_0$ | 初始位移 | $x(0)$ |
| $v_0$ | 初始速度 | $\dot{x}(0)$ |
| $\omega_n$ | 无阻尼固有圆频率 | rad/s |
| $\omega_d$ | 阻尼固有圆频率 | rad/s，通常用于欠阻尼系统 |
| $T_n$ | 固有周期 | s |
| $f_n$ | 固有频率 | Hz |
| $\zeta$ | 阻尼比 | 无量纲 |
| $\lambda$ | 特征根或特征值 | 决定指数响应和稳定性 |
| DOF | Degree of Freedom，自由度 | 独立运动坐标数 |
| SDOF | Single Degree of Freedom，单自由度 | 一个独立坐标 |
| 2DOF | Two Degrees of Freedom，二自由度 | 两个独立坐标 |
| MDOF | Multi-Degree of Freedom，多自由度 | 多个独立坐标 |
| ODE | Ordinary Differential Equation，常微分方程 | MATLAB `ode23`、`ode45` 的求解对象 |
| TMD | Tuned Mass Damper，调谐质量阻尼器 | 振动控制装置 |

## 9. 复习建议

优先掌握以下高频词汇及其相互关系：

1. **mass–stiffness–damping**：质量、刚度、阻尼构成 SDOF 振动模型的三个基本要素；
2. **natural frequency–damping ratio–damped natural frequency**：固有圆频率、阻尼比和阻尼固有圆频率决定自由响应的基本形态；
3. **free vibration–forced vibration**：区分初始扰动响应与持续激励响应；
4. **transient response–steady-state response**：区分暂态部分和长期稳态部分；
5. **modeling–governing equation–solution–interpretation**：掌握从建模到工程解释的完整分析流程；
6. **state-space–ODE solver–time history**：掌握 MATLAB 数值仿真的基本工作链条。

## 10. Lecture 02：强迫响应与频率响应

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| forced response | 强迫响应 | 外部持续激励 $F(t)$ 作用下的系统响应 |
| homogeneous solution | 齐次解 | 运动方程齐次部分的解，等同于由初始条件引起的自由响应 |
| particular solution | 特解 | 满足外部激励的响应部分，通常对应稳态响应 |
| steady-state response | 稳态响应 | 激励持续足够长时间后保留下来的周期响应 |
| transient response | 瞬态响应 | 随时间衰减的初始条件响应 |
| harmonic excitation | 简谐激励 | 单一频率的正弦或余弦激励 |
| frequency ratio | 频率比 | $r=\omega/\omega_n$，激励频率与固有频率之比 |
| static deflection | 静态位移 | $\delta_{st}=F_0/k$，同样大小的恒定力产生的位移 |
| magnification factor | 幅值放大系数 | $M=X/\delta_{st}$，衡量动态响应相对静态响应的放大程度 |
| frequency response function (FRF) | 频率响应函数 | 输入与输出复幅值随频率变化的关系 |
| transfer function | 传递函数 | 线性系统在拉普拉斯域或频域中的输入/输出比 |
| phase lag | 相位滞后 | 响应相对于激励的相位延迟 |
| resonance frequency | 共振频率 | 频率响应幅值达到峰值的频率，低阻尼时约为固有频率 |
| resonant peak | 共振峰 | 频率响应曲线中的最大幅值 |
| beating | 拍振 | 两个接近频率叠加导致的周期性振幅起伏 |
| bounded-input-bounded-output (BIBO) stability | 有界输入有界输出稳定性 | 有界激励只产生有界响应的稳定性判据 |
| pole | 极点 | 传递函数分母为零的位置，与系统特征根和动态稳定性相关 |

## 11. 基座激励、隔振与测量

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| base excitation | 基座激励 | 支承或地基位移/加速度作为系统输入的激励 |
| absolute displacement | 绝对位移 | 相对于惯性参考系测量的位移 $x(t)$ |
| relative displacement | 相对位移 | 质量块相对于基座的位移 $z=x-y$ |
| displacement transmissibility | 位移传递率 | $T_d=X/Y$，基座位移传递到质量块的幅值比 |
| transmissibility | 传递率 | 输入与输出响应幅值的比值，常用于隔振评价 |
| vibration isolation | 振动隔离 | 通过降低传递率减少振动向设备或结构传递 |
| accelerometer | 加速度计 | 利用质量块相对位移估计基座或结构加速度的仪器 |
| seismometer | 地震仪 | 通过惯性质量测量地面位移或地震运动的仪器 |
| inertial sensor | 惯性传感器 | 以惯性参考测量位移、速度或加速度的传感器 |
| piezoelectric ceramic | 压电陶瓷 | 将机械振动转换为电信号的传感元件材料 |

## 12. 阻尼识别、转子与周期激励

| 英文术语 | 中文含义 | 讲义中的用法或理解 |
| --- | --- | --- |
| half-power method | 半功率法 | 从稳态频率响应峰值两侧的半功率频率估计阻尼比 |
| half-power frequency | 半功率频率 | 幅值为共振峰值 $1/\sqrt{2}$ 的频率 $\omega_1,\omega_2$ |
| bandwidth | 半功率带宽 | $\Delta\omega=\omega_2-\omega_1$，反映共振峰宽度 |
| Q-factor | 品质因数 | $Q=\omega_n/\Delta\omega\approx1/(2\zeta)$，衡量共振尖锐程度 |
| structural damping | 结构阻尼 | 由材料内部摩擦和循环应力滞回造成的能量耗散 |
| hysteresis | 滞回 | 加载与卸载路径不重合，包围的滞回环代表能量损失 |
| complex stiffness | 复刚度 | 用 $k^*=k(1+i\gamma)$ 表示结构阻尼的模型 |
| unbalanced mass | 不平衡质量 | 转子质量中心偏离旋转轴线而产生周期惯性力 |
| unbalanced force | 不平衡力 | 与偏心距和转速平方成正比的旋转激励 |
| rotating shaft | 旋转轴 | 承受转子不平衡力并可能发生横向振动的轴件 |
| whirling | 涡动 | 旋转轴中心线或转子质心绕平衡位置回转的运动 |
| synchronous whirl | 同步涡动 | 涡动角速度与转子旋转角速度相同 |
| asynchronous whirling | 异步涡动 | 涡动与转子旋转不同步，质心常沿椭圆轨迹运动 |
| critical speed | 临界转速 | 转速接近横向固有频率、响应显著放大的转速 |
| Fourier series | 傅里叶级数 | 将周期激励分解为基频及整数倍频谐波的表示 |
| fundamental frequency | 基频 | 周期信号的最低非零频率 $\omega_0=2\pi/T$ |
| harmonic | 谐波 | 基频整数倍的频率分量 |
| Fourier coefficient | 傅里叶系数 | 描述各正弦、余弦谐波幅值的系数 $a_p,b_p$ |
| superposition principle | 叠加原理 | 线性系统各谐波响应可逐项求解并相加 |

## 13. Lecture 02 常用符号

| 符号 | 含义 | 常见单位或说明 |
| --- | --- | --- |
| $F_0$ | 简谐外力幅值 | N |
| ω | 激励圆频率 | rad/s |
| φ | 激励/响应相位差 | rad |
| $r$ | 频率比 | $r=\omega/\omega_n$ |
| $M$ | 幅值放大系数 | $M=X/\delta_{st}$ |
| $H(i\omega),G(i\omega)$ | 频率响应函数/传递函数 | 复数，包含幅值与相位 |
| $T_d$ | 位移传递率 | $T_d=X/Y$ |
| $z(t)$ | 质量块相对基座位移 | $z=x-y$ |
| ω_r | 共振频率 | (\omega_r=\omega_n\sqrt{1-2\zeta^2})（小阻尼时） |
| Δω | 半功率带宽 | Δω=ω_2-ω_1 |
| $Q$ | 品质因数 | $Q\approx1/(2\zeta)$ |
| γ | 结构阻尼损耗因子 | 复刚度 (k^*=k(1+i\gamma)) 中的无量纲参数 |
| $a_0,a_p,b_p$ | 傅里叶系数 | 分别对应直流项、余弦项和正弦项 |
