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

卸载定律；材料在卸载过程中应力应变呈现线性关系

冷作硬化

对于没有明显屈服极限的材料，将塑性变形为0.2%时的应力称为名义屈服强度

压缩时屈服阶段和弹性阶段是一样的

压缩破坏阶段端面一般接近45度，说明破坏主要是由剪切造成的，脆性材料更能受压，故我们经常将脆性材料用在受压的情景下，比如车床底部。

失效、安全系数和强度计算

脆性材料给的安全因数比较保守，是因为脆性材料断裂前没有明显的变形
#box(theme: "example", title: "Example", [
  
])

#box(theme: "info",title: "Notes", [
 替代定理：如果一端口网络两端电压已知，则可以用一个电压源代替，而对电路的其他部分没有影响。同样如果电流已知则可以用电流源代替。
])