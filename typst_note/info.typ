#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "信息理论",
  author: "彧君"
)

#set text(font: ("Inter", "KaiTi"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[信息理论] \
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
= Lecture 1
== 信息的度量
一个事件的信息量大小，取决于这个事件发生的概率。

*大概率事件*：发生的可能性大，一旦发生，比较意料之中，带来的信息量少

*小概率事件*：发生的可能性小，一旦发生，带来的信息量大

信息量可以用以下公式表示：
$ I(x) = log_a ( 1 / P(x) ) = -log_a P(x) $

- 为什么是log函数

  - 概率越小，可能性越大
  - 可加性
  - 非负数

- 确定事件，信息量为0
- 不可能发生的事件，信息量为无穷大

#box(theme: "info",title: "Snippets", [
 1. 你能提出来和你能理解是两码事。
 2. 香农奖的第一任获奖者是香农。
])

#box(theme: "example", title: "Example", [
  对于一个$N times N$的像素网格，其所带的信息量是$8 times N^2$：

  pf:对于8位2进制，能够表示256种颜色，对于一个像素而言，他是某个颜色的概率是$1/256$，那对于$N times N$的网格就是$8 times N^2$
])

#box(theme: "info",title: "Notes", [
 BUG：猫的照片，狗的照片，马赛克照片喂给神经网络，其对他们的理解是不同的。

忽略了信息的重要性，虽然在通信领域没有任何问题。
])

= 随机变量的熵和互信息
== 概率论基础

随机变量的概率空间 ${X, cal(X), q(x)}$

- $cal(X)$: $X$ 的取值空间, $cal(X) = {x_k; k = 1, 2, dots.c, K}$
- $q(x)$: 事件 ${X = x}$ 发生的概率, $q(x) >= 0, sum_(x in cal(X)) q(x) = 1$


联合变量对 $(X, Y)$

二维随机变量 ${(X, Y), cal(X) times cal(Y), p(x, y)}$

- $p(x, y) = P{X = x, Y = y}$
- $cal(X) = {x_k; k = 1, 2, dots.c, K}, cal(Y) = {y_j; j = 1, 2, dots.c, J}$

- $p(x_k, y_j) >= 0$
- $sum_k sum_j p(x_k, y_j) = 1$
- $sum_k p(x_k, y_j) = omega(y_j)$
- $sum_j p(x_k, y_j) = q(x_k)$

条件概率

$ p(y_j | x_k) = p(Y = y_j | X = x_k) = frac(p(x_k, y_j), q(x_k)) $

$ p(x_k | y_j) = p(X = x_k | Y = y_j) = frac(p(x_k, y_j), omega(y_j)) $

== 事件的自信息
信息量是信息论的重要概念，事件的信息量基于该事件发生的概率。

定义：对于概率空间 ${X, cal(X), q(x)}$，事件 ${X = x_k}$ 的自信息定义为

$ I(x_k) = - log_a q(x_k) $

单位：当 $a = 2$ 时，为比特(bit)，当 $a = e$ 时，为奈特(nat)。

定义为概率的负对数的优点：
+ 符合概率越小，信息量越大的要求。
+ 对数函数是比较简单的函数，容易进行数学处理。
+ 对数函数的可加性符合生活中关于信息可叠加性的经验。

=== 事件自信息的#text(fill: blue)[本质]

+ 事件发生后对外界（观察者）所提供的信息量。
+ 事件发生前外界（观察者）为确认该事件的发生所需要的信息量，也是外界为确认该事件所需要付出的代价。
+ 事件的自信息并不代表事件的不确定性，事件本身没有不确定性可言，它要么是观察的假设和前提，要么是观察的结果。

事件条件自信息的定义

二维随机变量 ${(X, Y), cal(X) times cal(Y), p(x, y)}$

事件 ${Y = y_j}$ 发生的条件下事件 ${X = x_k}$ 的条件自信息定义为：

$ I(x_k | y_j) = - log p(x_k | y_j) $

事件条件自信息的本质

+ 事件 ${Y = y_j}$ 发生后，${X = x_k}$ 如果再发生需要的“新”的信息量。
+ 事件 ${Y = y_j}$ 发生后，如果 ${X = x_k}$ 又发生了，则提供给观察者的“新”的信息量。

事件的互信息

二维随机变量 ${(X, Y), cal(X) times cal(Y), p(x, y)}$，事件 ${Y = y_j}$ 与事件 ${X = x_k}$ 之间的互信息定义为：

$ I(x_k ; y_j) = I(x_k) - I(x_k | y_j) = - log q(x_k) - {- log p(x_k | y_j)} $

事件互信息的本质

事件 ${Y = y_j}$ 发生后对事件 ${X = x_k}$ 不确定性的降低。

事件互信息的性质

#text(fill: blue)[对称性] $I(x_k ; y_j) = I(y_j ; x_k)$

$ log frac(p(x_k | y_j), q(x_k)) = log frac(p(x_k, y_j), q(x_k) omega(y_j)) = log frac(p(y_j | x_k), omega(y_j)) $

互信息对称性的完整推导过程：

$ I(x_k ; y_j) &= I(x_k) - I(x_k | y_j) \
               &= - log q(x_k) - (- log p(x_k | y_j)) \
               &= log frac(p(x_k | y_j), q(x_k)) \
               &= log frac(p(x_k, y_j) / omega(y_j), q(x_k)) quad &text("（应用条件概率公式）") \
               &= log frac(p(x_k, y_j), q(x_k) omega(y_j)) $

事件联合自信息的定义

#text(fill: blue)[二维随机变量] ${(X, Y), cal(X) times cal(Y), p(x, y)}$

事件 ${Y = y_j}$ 和 ${X = x_k}$ 的联合自信息定义为：

$ I(x_k, y_j) = - log p(x_k, y_j) $

表示事件 ${X = x_k}$ 和 ${Y = y_j}$ 同时发生需要的信息量，或者同时发生后对外界提供的信息量。

在给定 $Z = z$ 的条件下，事件 $X = x$ 与 $Y = y$ 之间的条件互信息为：

$ I(x; y|z) = log frac(p(x|y, z), p(x|z)) = log frac(p(x, y|z), p(x|z) dot p(y|z)) $

事件的条件互信息

表示事件 $Z = z$ 发生时，事件 $X = x$ 与 $Y = y$ 相互之间提供的信息量。

#text(fill: blue)[例子：] $x$: 杭州下雨，$y$: 上海下雨，$z$: 宁波下雨。

- $q(x) = q(y) = q(z) = 0.125$
- $p(x|y) = 0.25, p(x|z) = 0.25, p(y|z) = 0.25$
- $p(x|y, z) = 0.5$

则 $I(x) = 3 "bit", I(x|y) = 2 "bit", I(x; y) = 1 "bit"; I(x; y|z) = 1 "bit"$

联合事件互信息

#text(fill: blue)[定义：] 联合事件 ${Y = y, Z = z}$ 与事件 ${X = x}$ 之间的互信息为：

$ I(x; y, z) = log frac(p(x|y, z), p(x)) = log frac(p(x, y, z), p(x) p(y, z)) $

表示事件 ${Y = y, Z = z}$ 联合提供给事件 ${X = x}$ 的信息量

#text(fill: blue)[例子：] $x$: 杭州下雨，$y$: 上海下雨，$z$: 宁波下雨。

$I(x)$: 杭州下雨需要的信息量，$I(x; y, z)$: 上海下雨和宁波下雨这两个事件同时提供给杭州下雨这个事件的信息量。

$q(x) = 0.125; p(x|y) = 0.25$, 则

$ I(x; y) = I(x) - I(x|y) = 1 $

$p(x|y, z) = 0.5$, 则

$ I(x; y, z) = I(x) - I(x|y, z) = 2 > I(x; y) $

随机变量熵

定义：随机变量的熵定义为随机变量各个事件的平均自信息：

$ H(X) = E[I(X)] = sum_(x in cal(X)) q(x) I(x) = - sum_(x in cal(X)) q(x) log q(x) $

熵与自信息的#text(fill: blue)[区别]：熵针对的是随机变量，自信息针对具体的事件。

---

// [此处为二元熵函数 H(p) 的图像：一个开口向下的抛物线形状，顶点在 (0.5, 1)，过原点 (0, 0) 和 (1, 0)]

[例子]：二元随机变量 $X$ 的概率分布 $q(x_1) = p, q(x_2) = 1 - p$，则

$ H(X) = -p log p - (1 - p) log (1 - p) $

$p = 0, 1; H(X) = 0$ 确定性变量的熵为0。
$p = 0.5; H(X) = 1$ 等概率变量的随机性最大，所以熵最大。


随机变量的联合熵

#align(center)[
          #math.equation(
            block: true,
            $ H(X, Y) = E[I(X, Y)] = - sum_(x in cal(X), y in cal(Y)) p(x, y) log p(x, y) $
          )
        ]

#let highlight-box(title, body, color: rgb("#f3f6f3"), stroke-color: rgb("#116514")) = block(
  width: 100%,
  fill: color,
  stroke: (left: 4pt + stroke-color),
  inset: 12pt,
  radius: 2pt,
  [
    #text(weight: "bold", fill: stroke-color, size: 12pt)[#title]
    #v(4pt)
    #body
  ]
)

= 随机变量的条件熵对比

== 两个核心定义的区别

#highlight-box("1. 给定“特定取值”时的条件熵：H(X|y)", color: rgb("#f8f9fa"), stroke-color: rgb("#495057"))[
  *含义*：表示当随机变量 $Y$ 已经取了某一个**具体的、确定的值** $y$ 时，随机变量 $X$ 仍然保留的不确定性。它是一个局部的、特定事件下的度量。
  
  $ H(X|y) = - sum_(x in cal(X)) p(x|y) log p(x|y) $
]

#v(1em)

#highlight-box("2. 给定“随机变量”时的条件熵：H(X|Y)", color: rgb("#eef5ee"), stroke-color: rgb("#116514"))[
  *含义*：表示在已知整个随机变量 $Y$ 的情况下，随机变量 $X$ 的**平均不确定性**。它是一个全局的、宏观的期望值。
  
  $ H(X|Y) = - sum_(x in cal(X)) sum_(y in cal(Y)) p(x, y) log p(x|y) $
]

---

== 数学推导与内在联系

定义 2 实际上是由定义 1 对概率分布 $p(y)$ 求数学期望推导而来的。推导过程如下：

条件熵 $H(X|Y)$ 是具体的条件熵 $H(X|y)$ 的加权平均（期望）：
$ H(X|Y) = bb(E)_Y [H(X|y)] = sum_(y in cal(Y)) p(y) H(X|y) $

将 $H(X|y)$ 的定义式代入上式：
$ H(X|Y) = sum_(y in cal(Y)) p(y) [ - sum_(x in cal(X)) p(x|y) log p(x|y) ] $

提取负号并合并求和号：
$ H(X|Y) = - sum_(x in cal(X)) sum_(y in cal(Y)) p(y) p(x|y) log p(x|y) $

根据概率论中的乘法公式（联合概率与条件概率的关系）：$p(x, y) = p(y) p(x|y)$，代入即可得到最终形式：
$ H(X|Y) = - sum_(x in cal(X), y in cal(Y)) p(x, y) log p(x|y) $

= 熵的性质

$ H(X) eq.delta H_K(p_1, p_2, dots.c, p_K) eq.delta H_K(P) $
$ = - sum_(k=1)^K p_k log p_k $

+ $H_K(P)$ 对概率矢量 $P$ 的分量是对称的。
+ 非负性，即 $H_K(P) >= 0$。
+ 确定性，即若 $P = (p_1, p_2, dots.c, p_K)$ 中有一个分量为1，其余均为零，则 $H_K(P) = 0$。
+ 可扩展性，即 $lim_(epsilon -> 0) H_(K+1)(p_1, p_2, dots.c, p_K - epsilon, epsilon) = H_K(p_1, p_2, dots.c, p_K)$，这个可以这样理解：当佳航一个概率很小的事情，对总体的熵没有影响。