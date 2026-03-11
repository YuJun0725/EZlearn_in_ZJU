#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "心理学及应用",
  author: "彧君"
)

#set text(font: ("Times New Roman", "KaiTi"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[心理学及应用] \
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
== 记忆
三级信息加工模型：记忆的保持时间不同

#align(center)[
  #image("mind_pic/sanji.png", width: 70%)
]

记忆容量最有限的是短时记忆

*工作记忆：*完成当下工作所需要的记忆的集合，更像一个操作台，即有感觉记忆（外部）的输入也有长时记忆（内部）的输入。记忆容量非常有限。

工作记忆容量有限的神经机制：

理论一：受限于前额叶的代谢功能（可以通过人为加强提高记忆能力）

理论二：受限于脑区间信息交互的模式

- 长时记忆
  - 外显记忆
    - 语义记忆
    - 情景记忆  
  - 内隐记忆（不会意识到的）
    - 条件反射
    - 程序性记忆
    - 启动效应

不同记忆类型之间会进行转换，比如游泳，你在刚学的时候由于不熟悉，所以是情景记忆，如果是在书上看到则是语义记忆。
当你已经学得很熟了，那就转化为了程序记忆。

多样的记忆系统：

信息编码：输入途径不同

组块效应：比如记忆电话号码，一般是xxx-xxxx-xxxx

信息保持：存储时间不同

信息提取：回忆过程不同

位置序列效应


提高记忆表现

策略优化

遗忘规律和复习策略、测试比复习效果好、相似性编码比差异性编码效果好、分散学习收益更大、记忆提取的位置效应
#align(center)[
  #image("mind_pic/weizhi.png", width: 70%)
]


人类记忆的复杂性

主动构建
- 省略细节，提取主旨
- 根据按时构建记忆
- 根据经验重构信息

记忆提取
- 舌尖效应（大脑在进行记忆提取时出现的一种“临时短路”）
- 错误提取

记忆纠缠
- PTSD
  - 闯入性记忆

AI出现将重塑认知习惯，因为我们在使用AI的时候多数都是做判断题而不是简答题


舌尖效应

错误提取


自我验证的预言
#box(theme: "example", title: "Example", [
  对于一个$N times N$的像素网格，其所带的信息量是$8 times N^2$：

  pf:对于8位2进制，能够表示256种颜色，对于一个像素而言，他是某个颜色的概率是$1/256$，那对于$N times N$的网格就是$8 times N^2$
])

#box(theme: "info",title: "Notes", [
米勒定律：米勒通过实验发现，普通人的短时记忆在没有任何辅助手段（如反复背诵或做笔记）的情况下，一次只能记住大约 **5 到 9 个（即 7±2 个）**信息单位。
])