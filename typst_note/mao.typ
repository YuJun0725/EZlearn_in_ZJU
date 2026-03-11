#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "毛概",
  author: "彧君"
)

#set text(font: ("Inter", "KaiTi"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[毛概] \
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
= 马克思主义中国化



= 毛泽东思想
== 形成与发展
受到俄国革命的影响

毛泽东思想活的灵魂：实事求是、群众路线、独立自主

#box(theme: "example", title: "Example", [
  
])

#box(theme: "info",title: "Notes", [
 
])