#import "@preview/typsidian:0.0.3": *

#let note-title = "课程笔记"
#let course-name = "课程名称"
#let subtitle = "Lecture Notes"
#let author-name = "yujun"
#let semester = "2025-2026 学年"
#let instructor = "任课教师"
#let update-date = "2026-03-14"

#show: typsidian.with(
  title: note-title,
  course: course-name,
  author: author-name,
)

#set page(
  paper: "a4",
  margin: (x: 1.8cm, y: 1.6cm),
)

#set par(justify: true, leading: 0.8em)
#set text(font: ("Times New Roman", "KaiTi", "New Computer Modern"), lang: "zh", size: 10.8pt)
#set heading(numbering: "1.")

#show heading.where(level: 1): it => block(above: 1.4em, below: 0.8em)[
  #set text(size: 1.55em, weight: "bold")
  #it
]

#show heading.where(level: 2): it => block(above: 1.1em, below: 0.55em)[
  #set text(size: 1.2em, weight: "semibold")
  #it
]

#show heading.where(level: 3): it => block(above: 0.9em, below: 0.4em)[
  #set text(size: 1.02em, weight: "medium")
  #it
]

#let meta-item(label, value) = [
  #text(weight: "semibold")[#label：]
  #value
]

#let note-box(title, body, fill-color: luma(245), stroke-color: luma(205)) = block(
  inset: 0.9em,
  outset: 0.2em,
  radius: 8pt,
  fill: fill-color,
  stroke: 0.6pt + stroke-color,
)[
  #text(weight: "semibold")[#title]
  #v(0.45em)
  #body
]

#let key-point(body) = note-box(
  "Key Point",
  body,
  fill-color: rgb("#EEF6FF"),
  stroke-color: rgb("#B8D7F5"),
)

#let example(body) = note-box(
  "Example",
  body,
  fill-color: rgb("#F7F2E8"),
  stroke-color: rgb("#E2D0A7"),
)

#let notes(body) = note-box(
  "Notes",
  body,
  fill-color: rgb("#F3F3F3"),
  stroke-color: rgb("#D6D6D6"),
)

#let theorem(name, body) = note-box(
  "Theorem" + if name != "" [ " (" + name + ")" ] else [],
  body,
  fill-color: rgb("#EEF8F0"),
  stroke-color: rgb("#B9D9C0"),
)

#let formula-box(body) = block(
  inset: (x: 1em, y: 0.7em),
  fill: rgb("#FCFCFC"),
  stroke: 0.5pt + luma(210),
  radius: 6pt,
)[#align(center)[#body]]

#align(center)[
  #block(inset: 1.8em)[
    #text(size: 2.2em, weight: "bold")[#note-title]
    #v(0.45em)
    #text(size: 1.15em, style: "italic")[#subtitle]
    #v(1.1em)
    #line(length: 70%, stroke: 0.8pt + luma(170))
    #v(1.1em)
    #grid(
      columns: (auto, auto),
      gutter: (2.2em, 0.6em),
      align: left,
      [#meta-item("课程", course-name)], [#meta-item("作者", author-name)],
      [#meta-item("学期", semester)], [#meta-item("教师", instructor)],
      [#meta-item("更新", update-date)], [#meta-item("用途", "课堂笔记 / 复习整理")],
    )
  ]
]

#v(1.4em)
#line(length: 100%, stroke: 0.6pt + luma(190))
#pagebreak()

#outline(title: "Contents", depth: 3)
#pagebreak()

= 课程概览

== 学习目标

- 这一门课主要解决什么问题
- 课程的核心知识模块
- 复习时最值得优先掌握的内容

== 先修知识

- 前置课程 1
- 前置课程 2
- 建议复习的基础概念

== 资料清单

- 教材：
- PPT：
- 作业：
- 参考链接：

#key-point[
这里写整门课最重要的总纲，适合在考前快速回看。
]

= Lecture 1 标题

== 本讲摘要

这里先用 3 到 5 句话概括这一讲讲了什么、和上一讲如何衔接、最重要的结论是什么。

== 核心概念

=== 概念 1

定义、条件、性质、适用范围。

#formula-box[$
  F = m a
$]

=== 概念 2

- 要点 1
- 要点 2
- 要点 3

#notes[
这里适合写容易混淆的点、老师强调的话、和其它知识点的区别。
]

== 推导与证明

=== 推导思路

1. 从已知条件出发。
2. 做必要的等价变形。
3. 得到最终表达式并解释物理或数学意义。

#theorem("可选标题")[
定理、结论、命题都可以放在这里。
]

== 例题

#example[
题目：这里写例题题意。

解题步骤：
1. 写出已知量和未知量。
2. 选公式或方法。
3. 代入计算。
4. 检查单位、数量级和结论是否合理。

答案：这里写最终结果。
]

== 图表与补充

// #align(center)[
//   #image("example.png", width: 65%)
// ]

图下说明：解释这张图为什么重要，应该观察哪些变量关系。

= Lecture 2 标题

== 本讲摘要

延续上面的结构继续写。

= 期末复习

== 高频考点

- 高频考点 1
- 高频考点 2
- 高频考点 3

== 易错点

- 易错点 1
- 易错点 2
- 易错点 3

== 一页速记

#key-point[
把全书最关键的定义、公式、结论压缩在这里，方便最后冲刺。
]
