#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "工程流体力学",
  author: "彧君"
)

#set text(font: ("Inter", "KaiTi"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[工程流体力学] \
    #v(0.5em)
    #text(style: "italic", size: 1.2em)[彧君]
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

大量分子

热运动

分子作用力

以流体质点作为研究对象

没有空间尺寸，但是有物理量，并且是时间和空间的函数。

流体具有可压缩性和热膨胀性，气体更为明显

*流体质点*

*流体的物理量*

密度、比体积、相对密度
$ rho = d m / d V $
$ v = V / m = 1 / rho $
$ d = rho / rho_"ref" $
流体的膨胀性和压缩性

相比于液体来说，气体具有状态方程：

$ p V=m R_g T $
除了方程表示法之外，还有系数表示法

1.膨胀系数
$ alpha_v = 1/V (d V) / (d T) |_p $
气体的等压膨胀系数
$ alpha_v = 1/T $
2.体积压缩率
$ kappa = - 1/V (d V) / (d p) |_T $
气体的等温压缩率
$ kappa = 1/p $
3.体积模量
$ K = 1 / kappa = - V (d p) / (d V) |_T $
压缩性

不可压缩流体

$ rho = "Constant" $

可压缩流体：如子弹在高速运动的时候
== 流体的粘性
原因：
- 分子之间吸引力
- 不规则热运动
- 不断的动量交换
=== 牛顿摩擦定律
摩擦力
$ F = mu v_0/delta A $
可以据此得到切应力
$ tau = F/A = mu v_0/delta $
实际上，$v_0/delta$指的是速度梯度，公式写得更准确一点：
$ tau = plus.minus mu (d v)/ (d y) $
=== 流体的粘度
动力粘度
$ mu = tau / ((d u) / (d y)) $
运动粘度
$ nu = mu/rho $  

#box(theme: "example", title: "Example", [
  
])

