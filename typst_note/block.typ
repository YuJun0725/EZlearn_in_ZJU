#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "区块链技术与实践",
  author: "彧君"
)

#set text(font: ("Inter", "KaiTi"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[区块链技术与实践] \
    #v(0.5em)
    #text(style: "italic", size: 1.2em)[yujun]
  ]
]
#line(length: 100%, stroke: 0.5pt + gray)
#v(2em)

#set text(font: "New Computer Modern")



#outline(
  title: "目 录",
  indent: auto,
  depth: 3,
)

#pagebreak()

== 共识

=== 拜占庭共识

*拜占庭将军问题*

由 Lamport 等人于 1982 年提出。问题描述：若干将军分率军队包围敌城，必须达成一致行动（全部进攻或全部撤退），但其中可能存在*叛徒*（发送矛盾信息的节点）。如何在存在叛徒的情况下，使忠诚将军仍能达成一致？

这是分布式系统中*节点可能发送任意错误消息*（即拜占庭故障）场景的抽象模型。

*结论*：若总节点数为 $n$，拜占庭故障节点数为 $f$，则需满足：
$ n >= 3f + 1 $

即拜占庭故障节点数不能超过总节点数的 $1/3$，才能保证达成正确共识。

*PBFT（实用拜占庭容错）*

PBFT 由 Castro 和 Liskov 于 1999 年提出，是第一个在实际系统中可用的拜占庭容错算法。

*三阶段协议流程*：

+ *Pre-prepare（预准备）*：主节点（Leader）收到客户端请求后，向所有副本节点广播预准备消息，附带消息序号和内容摘要。

+ *Prepare（准备）*：副本节点收到预准备消息后，若验证通过则向所有其他节点广播准备消息。每个节点收集到 $2f$ 个相同准备消息后，进入 prepared 状态。

+ *Commit（提交）*：节点进入 prepared 状态后广播提交消息。收集到 $2f+1$ 个提交消息后，执行请求并回复客户端。

#box(theme: "info", title: "Notes", [
  PBFT 保证了两个核心性质：
  - *Safety（安全性）*：诚实节点不会对同一序号的请求提交不同结果
  - *Liveness（活性）*：只要故障节点不超过 $f$ 个，系统最终能处理请求
])

*PBFT 的复杂度与局限*：

- 通信复杂度为 $O(n^2)$，每轮共识需要节点间大量消息交互
- 适合节点数较少（几十个）的许可链场景，不适合大规模公链
- 需要已知参与节点集合，节点动态加入/退出需额外机制处理

*视图变更（View Change）*

当主节点出现故障或超时无响应时，副本节点触发视图变更协议，选出新的主节点，保证系统持续运行。
