#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "设计与制造2",
  author: "彧君"
)

#set text(font: ("Inter", "Microsoft YaHei"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[设计与制造] \
    #v(0.5em)
    #text(style: "italic", size: 1.2em)[彧君]
  ]
]
#line(length: 100%, stroke: 0.5pt + gray) // 画一条 Obsidian 风格的分隔线
#v(2em)

#outline(
  title: "目 录",
  indent: auto,       // 自动缩进
  depth: 3,           // 只显示到三级标题（=, ==, ===）
)

#pagebreak()
= 平面构建
== 自由度
确定各构件相对位置所需要的独立参数数目。
机构具有确定相对运动的条件：

主动件数目=自由度>0

平面低副

局部自由度，一般是要剔除的

虚约束

平面机构的高副低代

#box(title: "Box", [
  #lorem(50)
])

#box(theme: "example", title: "Example", [
  #lorem(50)
])
