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