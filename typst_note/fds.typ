#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "Foundation of Data Structure",
  author: "彧君"
)

#set text(font: ("Times New Roman", "KaiTi"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[Foundation of Data Structure] \
    #v(0.5em)
    #text(style: "italic", size: 1.2em)[彧君]
  ]
]
#line(length: 100%, stroke: 0.5pt + gray) // 画一条 Obsidian 风格的分隔线
#v(2em)

#set text(font: "New Computer Modern") // 设置经典数学字体


#pagebreak()
#outline(
  title: "Content",
  indent: auto,       // 自动缩进
  depth: 3,           // 只显示到三级标题（=, ==, ===）
)

#pagebreak()
= Lecture One
== Algorithm Analysis

*Inout:*zero or more

*Output:*at least one

*Definiteness:*instruction must be clear and unambiguous

*Finiteness*

*Effectiveness*

The difference of PROGRAM and ALGORITHM:

A #text(fill: red)[program],program is written in some programming language, and does not have to be finite (e.g. an operation system).
An #text(fill: red)[algorithm] can be described by human languages, flow charts, some programming languages, or pseudo-code.

== What to analyse
run times

time and space complexities

我们通常并不是特别关心这个算法具体执行了几步，而更关心它的趋势。

Asymptotic Notation是用来算法复杂度描述随着输入数据规模N的增长而变化的趋势。

+ *大 O 记号 *
  - *数学定义*：$T(N) = O(f(N))$，如果存在正数常数 $c$ 和 $n_0$，使得对于所有 $N >= n_0$，都有 $T(N) <= c dot f(N)$。
  - *通俗理解*：它描述了算法复杂度的渐近上界。你可以把它理解为“算法在最坏情况下，运行时间也不会超过 $f(N)$ 的常数倍”。

+ *大 $Omega$ 记号 *
  - *数学定义*：$T(N) = Omega(g(N))$，如果存在正数常数 $c$ 和 $n_0$，使得对于所有 $N >= n_0$，都有 $T(N) >= c dot g(N)$。
  - *通俗理解*：它描述了算法复杂度的渐近下界。意思是“算法在最好情况下，运行时间至少也是 $g(N)$ 的常数倍”。

+ *大 $Theta$ 记号 *
  - *数学定义*：$T(N) = Theta(h(N))$，当且仅当 $T(N) = O(h(N))$ 并且 $T(N) = Omega(h(N))$。
  - *通俗理解*：它描述了算法复杂度的紧确界。意思是算法的运行时间与 $h(N)$ 的增长率是完全同量级的（既是它的上界，也是它的下界）。

+ *小 o 记号 *
  - *数学定义*：$T(N) = o(p(N))$，如果 $T(N) = O(p(N))$ 并且 $T(N) != Theta(p(N))$。
  - *通俗理解*：它描述了算法复杂度的严格上界。表示 $T(N)$ 的增长率严格且永远小于 $p(N)$ 的增长率，两者不在同一个量级。

#box(theme: "info",title: "Snippets", [
 - $2N + 3 = O(N) = O(N^(k >= 1)) = O(2^N) = dots$ \
  We shall always take the *smallest* $f(N)$.

- $2^N + N^2 = Omega(2^N) = Omega(N^2) = Omega(N) = Omega(1) = dots$ \
  We shall always take the *largest* $g(N)$.
])

*Asymptotic Rules：*

- *加法规则 (顺序执行)*：$T_1(N) + T_2(N) = max(O(f(N)), O(g(N)))$。
  如果你有两步操作，总复杂度取决于最慢的那一步（取最大值）。

- *乘法规则 (嵌套执行)*：$T_1(N) * T_2(N) = O(f(N) * g(N))$。
  如果你在一个循环里又写了一个循环，复杂度就是相乘。

- *多项式法则*：如果一个算法的时间是一个 $k$ 次多项式，那么你只需要看最高次项，它的复杂度就是 $Theta(N^k)$。
  你可以直接忽略所有的低次项和常数系数。

- *对数法则*：对于任意常数 $k$，都有 $log^k N = O(N)$。
  这是一个非常重要的结论，说明对数函数增长得非常缓慢，无论对数加上多少次方，在 $N$ 足够大时，它的增长速度永远比不上一次线性函数 $N$。

#box(theme: "example", title: "Example", [
  对于一个$N times N$的像素网格，其所带的信息量是$8 times N^2$：

  pf:对于8位2进制，能够表示256种颜色，对于一个像素而言，他是某个颜色的概率是$1/256$，那对于$N times N$的网格就是$8 times N^2$
])

#box(theme: "info",title: "Notes", [

])