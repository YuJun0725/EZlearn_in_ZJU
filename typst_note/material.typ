#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "材料力学",
  author: "彧君"
)

#set text(font: ("Inter", "KaiTi"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[材料力学] \
    #v(0.5em)
    #text(style: "italic", size: 1.2em)[yujun]
  ]
]
#line(length: 100%, stroke: 0.5pt + gray) // 画一条 Obsidian 风格的分隔线
#v(2em)

#set text(font: "New Computer Modern") // 设置经典数学字体



#outline(
  title: "目 录",
  indent: auto,       // 自动缩进
  depth: 3,           // 只显示到三级标题（=, ==, ===）
)

#pagebreak()
= Lecture One
== 基本假设

连续性假设：保证可以微分积分

均匀性假设：保证可以任意建坐标系

各向同性假设：保证可以任意建坐标系

小变形假设：视为线性形变

截面法求内力

= Lecture Two
== 拉伸压缩
切应力方向：对截面上一点取距，如果力矩方向是顺时针就是正，反之是负

截面角方向：从横截面开始，如果逆时针转到截面角则是正，反之是负

拉伸力方向：远离构件为正，反之是负

平截面假设可视为材料力学的基本公设之一

单轴应力状态

=== 力学性能

力学性能测试

实验条件：常温、静载、标准试件

样品中间细是为了让应力集中l=5d或l=10d

应力应变曲线
#align(center,image("material_pic/ylyb.png",width: 50%))

- 弹性阶段
比例极限、弹性极限

- 屈服阶段
上屈服强度、下屈服强度、屈服极限$sigma_s$

- 强化阶段
强度极限$sigma_b$

- 局部变形（颈缩）阶段

$sigma_s$和$sigma_b$是衡量材料力学性能的重要指标

塑性指标
断后伸长率、端面收缩率

卸载定律:材料在卸载过程中应力应变呈现线性关系

冷作硬化：材料的比例极限提高
#align(center,image("material_pic/xiezai.png",width: 50%))

对于没有明显屈服极限的材料，将塑性变形为0.2%时的应力称为名义屈服强度
#align(center,image("material_pic/minyi.png",width: 40%))
脆性材料没有屈服阶段和颈缩阶段，拉伸强度极限（约为140MPa）。它是衡量脆性材（铸铁）拉伸的唯一强度指标。
#align(center,image("material_pic/cuixin.png",width: 40%))

压缩时屈服阶段和弹性阶段是一样的

压缩破坏阶段端面一般接近45度，说明破坏主要是由剪切造成的，脆性材料更能受压，故我们经常将脆性材料用在受压的情景下，比如车床底部。

失效、安全系数和强度计算

脆性材料给的安全因数比较保守，是因为脆性材料断裂前没有明显的变形

塑性材料的压缩，前期屈服阶段和弹性阶段与拉伸一致，压缩时面积逐渐变大，但是不可能压断所以得不到压缩时的强度极限。
#align(center,image("material_pic/ya.png",width: 50%))

对于脆性材料，拉伸和压缩完全不一样，压缩强度远大于拉伸，并且当压缩断裂的时候，端面呈现大约45°。

#align(center,image("material_pic/cuixinya.png",width: 50%))

#box(theme: "example", title: "Example", [
  
])


== 胡克定律

== 正应力与应变 (轴向拉压)
在材料的*比例极限*（Proportional Limit）范围内，正应力 $sigma$ 与轴向应变 $epsilon$ 成正比。这是最经典的本构关系：

$ sigma = E dot epsilon $
或
$ Delta l = (F l)/(E A) $

其中：
- $sigma$: 正应力 (Stress)，单位为 $"Pa"$ 或 $N/m^2$；
- $epsilon$: 线应变 (Strain)，无量纲；
- $E$: 弹性模量 (Young's Modulus)，表征材料抵抗弹性变形的能力。

---

== 剪切形式的胡克定律
对于受剪切力作用的材料，在剪切比例极限内，剪应力 $tau$ 与剪应变 $gamma$ 存在如下关系：

$ tau = G dot gamma $

#block(
  fill: rgb("#f0f0f0"),
  inset: 10pt,
  radius: 4pt,
  [
    *各向同性材料的常数关系：*
    $G = E / (2(1 + nu))$
    其中 $nu$ 为泊松比 (Poisson's ratio)。
  ]
)

= 泊松比 (Poisson's Ratio)

== 定义与物理意义
当材料在某个方向受拉伸（或压缩）时，除了在该方向产生伸长（或缩短）外，在垂直于受力方向的横向也会发生收缩（或扩张）。**泊松比** $nu$（读作 Nu）定义为材料在单轴受载下，横向应变与轴向应变之比的负值：


  $ nu = - epsilon' / epsilon $


其中：
- $epsilon$: 轴向应变 (Axial Strain)；
- $epsilon'$: 横向应变 (Lateral Strain)；
- 负号确保了对于大多数普通材料（拉伸时横向收缩），泊松比为正值。

---

== 各向同性材料的取值范围
对于各向同性材料，泊松比的理论取值范围是：
$ -1 < nu < 0.5 $

是存在拉伸之后边宽的材料的，如一些**辅助材料 (Auxetics)**：$nu < 0$，即拉伸时横向反而变宽（如某些特种泡沫或蜂窝结构）。

---

== 与弹性常数的关系
在材料力学中，弹性模量 $E$、剪切模量 $G$ 与泊松比 $nu$ 之间存在紧密的耦合关系：

$ G = E / (2(1 + nu)) $

此外，体积模量 (Bulk Modulus) $K$ 可表示为：
$ K = E / (3(1 - 2nu)) $

#block(
  inset: (left: 10pt),
  stroke: (left: 2pt + gray),
  [_注：当 $nu = 0.5$ 时，$K$ 趋于无穷大，意味着材料体积在压力下完全不发生改变。_]
)
