#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "互换性与技术测量",
  author: "彧君"
)

#set text(font: ("Inter", "Microsoft YaHei"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[互换性与技术测量] \
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
= 序言
== 优先数和优先数系
*优先数*是一套经过科学设计的数值标准，用于规定产品的参数（如尺寸、功率、转速等）应该按什么样的比例来挑选。简而言之就是规定了一套标准供加工厂商能够按照它确定尺寸，能够保证零件的互换性。

*优先数系*是由一些十进制等比数列组成，代号为*Rr*（r取5，10,20,40,80等），其公比为$root(r, 10)$，这保证了在每个10进制区间都有r个优先数。

有时候因为生产的需要，就衍生出*派生数系*，代号为*Rr/p*，其公比为$root(r/p, 10)$。

#box(title: "Box", [
  #lorem(50)
])

#box(theme: "example", title: "Example", [
  #lorem(50)
])
