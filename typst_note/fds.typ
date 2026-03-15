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

*【Example】* Given (possibly negative) integers $A_1, A_2, ..., A_N$, find the maximum value of $sum_(k=i)^j A_k$.

#block(
  fill: luma(240),
  inset: 12pt,
  radius: 4pt,
  [
    ```c
    int MaxSubsequenceSum ( const int A[ ], int N )
    {
        int ThisSum, MaxSum, i, j, k;

    /* 1*/  MaxSum = 0; /* initialize the maximum sum */
    /* 2*/  for( i = 0; i < N; i++ ) /* start from A[ i ] */
    /* 3*/      for( j = i; j < N; j++ ) { /* end at A[ j ] */
    /* 4*/          ThisSum = 0;
    /* 5*/          for( k = i; k <= j; k++ )
    /* 6*/              ThisSum += A[ k ]; /* sum from A[ i ] to A[ j ] */
    /* 7*/          if ( ThisSum > MaxSum )
    /* 8*/              MaxSum = ThisSum; /* update max sum */
                } /* end for-j and for-i */
    /* 9*/  return MaxSum;
    }
    ```
  ]
)
这样的算法的时间复杂度是$T(N)=O(N^3)$，这个可以通过写出运行步骤数的求和公式得到。

显然这样的算法其实并不是最优解，
```c
for( k = i; k <= j; k++ )
  ThisSum += A[ k ]; 
```
这部分其实是一直在反复计算，浪费了资源。

    ```c
    int MaxSubsequenceSum ( const int A[ ], int N )
    {
        int ThisSum, MaxSum, i, j;

    /* 1*/  MaxSum = 0; /* initialize the maximum sum */
    /* 2*/  for( i = 0; i < N; i++ ) { /* start from A[ i ] */
    /* 3*/      ThisSum = 0;
    /* 4*/      for( j = i; j < N; j++ ) { /* end at A[ j ] */
    /* 5*/          ThisSum += A[ j ]; /* sum from A[ i ] to A[ j ] */
    /* 6*/          if ( ThisSum > MaxSum )
    /* 7*/              MaxSum = ThisSum; /* update max sum */
                } /* end for-j */
            } /* end for-i */
    /* 8*/  return MaxSum;
    }
    ```


=== 核心逻辑改进
- *优化点*：在 Algorithm 1 中，计算 $sum_{k=i}^j A_k$ 需要重新启动一个循环。而在 Algorithm 2 中，利用了数学等式：
  $ sum_(k=i)^j A_k = A_j + sum_(k=i)^(j-1) A_k $
- *效率提升*：通过在 `j` 循环中直接累加当前元素，消除了最内层的 `k` 循环。
- *时间复杂度*：$O(N^2)$。对于 $N=10,000$ 的数据规模，这比 $O(N^3)$ 要快得多。

Algorithm 3：Divide and Conquer

注：在fds这门课中的除法一般都是integer的除法。

将包含N个数字的序列从中间分成左右2分，则最大子序列只可能出现在三个地方：

- 左边序列
- 右边序列
- 横跨左右

对于左右序列，找到他们的最大子序列的时间复杂度是$T(N/2)$
，对于第三种情况，我们的算法是，从中间边界开始，先向左一直求和，得到最大的子序列，同理得到从中间向右最大的子序列，最后将这两个序列合并。

最后得到这种算法的时间复杂度是$T(N) = 2T(N/2)+c N$

求解该递推式

递推式时间复杂度求解：$T(N) = 2T(N/2) + c N$

这种递推式是分治算法（如最大子序列和的 Algorithm 3、归并排序等）的经典数学模型。求解该方程通常有两种经典方法：*展开法（迭代法）*和*主定理（Master Theorem）*。最终得出的时间复杂度为 *$O(N log N)$*。

方法一：展开法（代入法）

这种方法的核心思想是将递推式像剥洋葱一样一层层代入展开。为了方便计算，我们假设 $N$ 是 2 的整数次幂（即 $N = 2^k$），并且假设递归触底时的基本情况为 $T(1) = 1$。

+ *逐步展开方程*：
  已知原方程，将 $N/2$ 代入得 $T(N/2) = 2 T(N/4) + c(N/2)$，替换回原方程：
  $ T(N) &= 2 T(N/2) + c N \
         &= 2 [2 T(N/4) + c (N/2)] + c N \
         &= 4 T(N/4) + 2 c N $
  再往下展开一层求 $T(N/4)$ 并代入：
  $ T(N) &= 4 [2 T(N/8) + c (N/4)] + 2 c N \
         &= 8 T(N/8) + 3 c N $

+ *寻找通项规律*：
  观察可得通项公式为：
  $ T(N) = 2^k T(N/2^k) + k dot c N $

+ *代入边界条件*：
  当不断对半拆分直到只剩 1 个元素时，递归触底，即 $N / 2^k = 1$。
  此时可以推导得出 $N = 2^k$，两边取以 2 为底的对数得到 $k = log_2 N$。
  将 $k$ 和 $N/2^k$ 代回通项公式：
  $ T(N) &= N dot T(1) + (log_2 N) dot c N \
         &= N + c N log_2 N $

+ *得出大 O 复杂度*：
  *结论：时间复杂度为 $O(N log N)$*



将任务分成同样大小的两个任务并通过线性方式组合起来。

Algorithm 4: On-line Algorithm (Kadane's Algorithm)

#block(
  fill: luma(240),
  inset: 12pt,
  radius: 4pt,
  [
    ```c
    int MaxSubsequenceSum( const int A[ ], int N )
    {
        int ThisSum, MaxSum, j;
    /* 1*/  ThisSum = MaxSum = 0;
    /* 2*/  for ( j = 0; j < N; j++ ) {
    /* 3*/      ThisSum += A[ j ];
    /* 4*/      if ( ThisSum > MaxSum )
    /* 5*/          MaxSum = ThisSum;
    /* 6*/      else if ( ThisSum < 0 )
    /* 7*/          ThisSum = 0;
            } /* end for-j */
    /* 8*/  return MaxSum;
    }
    ```
  ]
)

核心原理解析

这个算法之所以被称为“在线处理 (On-line)”，是因为它只需要扫描数据一次。在任何时刻，算法都能对它已经读入的数据给出正确的解答（即读到第 $i$ 个数时，就知道前 $i$ 个数的最大子序列和）。

它的核心逻辑是：如果一个子序列的累加和是负数，那么它绝对不可能成为包含在更长最大子序列前面的“前缀”。

算法从头到尾遍历数组，不断把当前元素加到 `ThisSum` 中，并随时用 `ThisSum` 更新历史最高纪录 `MaxSum`。当 `ThisSum` 跌破 $0$ 时，说明这之前的这一段子序列变成了一个“累赘”。如果后面的序列带上这个负数前缀，总和只会比后面的序列本身更小。因此，算法果断地将 `ThisSum` 归零。

*时间复杂度*：$O(N)$。只有一个 `for` 循环，数组中的每个元素只被访问一次，这是线性时间复杂度，是解决此问题的理论下限。


== 抽象数据类型（Abstract Data Type，ADT）
Data Type = { Objects } ∪ { Operations }
数据类型不仅仅包含数据本身，还包含对该数据的操作。


= § 2 The List ADT (线性表抽象数据类型)

按照 ADT 的定义，我们将列表拆分为“对象”和“操作”两部分。

== 1. Objects (数据对象)
列表的数据对象就是一系列按逻辑顺序排列的元素集合：$("item"_0, "item"_1, ..., "item"_{N-1})$。
他们的物理内存是连续的。

== 2. Operations (基本操作规范)
有了数据，我们需要定义外部可以对这个列表发出哪些指令（即接口规范）：
- *基础管理*：获取列表长度 $N$、打印所有元素、创建一个空列表。
- *游标导航*：寻找当前元素的下一个 (next) 或上一个 (previous)。
- *增删查*：
  + *查找 (Find)*：找出列表中的第 $k$ 个元素 ($0 <= k < N$)。
  + *插入 (Insert)*：在第 $k$ 个元素**之后 (after)** 插入一个新元素。
  + *删除 (Delete)*：从列表中删除某个元素。

---

===  核心思考题解析：Why after? (为什么规定插入在“之后”？)

幻灯片右侧有一个引人注目的气泡提问：在定义“插入”操作的规范时，为什么要特意强调插入在第 $k$ 个元素的**“之后 (after)”**，而不是说“插入到第 $k$ 个位置”或者“插入在之前”？

这是数据结构设计中一个非常务实且精妙的考量，它为了照顾到底层**“单向链表 (Singly Linked List)”**的实现痛点：

1. *如果底层是数组*：插在第 $k$ 个元素的前面或后面，时间复杂度都是 $O(N)$，因为都要把后面的元素往后挪腾出空间，区别不大。
2. *如果底层是单向链表*：在单向链表中，每一个节点只牵着它“下一个”节点的手，它**不知道自己的“上一个”是谁**。
   - 如果规范要求插在当前节点*之后*：非常简单，只需要把新节点连向下一个节点，再把当前节点连向新节点即可，纯指针操作，时间复杂度 *$O(1)$*。
   - 如果规范要求插在当前节点*之前*：这就惨了。因为你不知道上一个节点在哪，你必须从链表的头部开始，顺藤摸瓜一路遍历找到当前节点的前驱节点，这需要耗费 *$O(N)$* 的时间。

*结论*：ADT 虽然强调“规范与实现分离”，但在制定规范时，设计者已经预判了底层实现的物理限制。将插入操作定义为“插入到之后”，既能满足向列表中添加元素的逻辑需求，又能确保在底层使用单链表实现时，能够写出最高效 ($O(1)$) 的代码。

== 1. Simple Array Implementation of Lists (列表的简单数组实现)

最直观实现列表的方法是使用编程语言中自带的数组（Array）。

=== 核心特征：顺序映射 (Sequential Mapping)
在物理内存中，数组是一块**连续**的存储空间。
逻辑上相邻的元素（如 $"item"_i$ 和 $"item"_{i+1}$），在物理内存地址上也是紧挨着的（如 `array + i` 和 `array + i + 1`）。

#table(
  columns: (1fr, 1fr),
  align: center,
  [*Address (内存地址)*], [*Content (存储内容)*],
  [$dots$], [$dots$],
  [`array + i`], [$"item"_i$],
  [`array + i + 1`], [$"item"_{i+1}$],
  [$dots$], [$dots$]
)

=== 优缺点分析

-  *缺点 1：容量固定 (MaxSize has to be estimated)*
  在 C 语言等底层语言中，简单数组在创建时必须提前声明大小。如果预估太小，数据装不下会溢出；如果预估太大，又会造成严重的内存浪费。

- *优点：极速的随机访问 (Find_Kth takes $O(1)$ time)*
  这是数组最大的杀手锏。因为内存是连续的，只要知道数组的首地址，想找第 $K$ 个元素，CPU 直接用数学公式 `首地址 + K * 元素大小` 就能一步精准定位，耗时永远是常量级 *$O(1)$*。

- *缺点 2：低效的插入与删除 (Insertion and Deletion take $O(N)$ time)*
  数组在增删数据时非常痛苦：
  - *插入*：如果要在中间插入一个新元素，必须把该位置及之后的所有元素都往后挪一个位置，腾出空间。
  - *删除*：如果删除了中间的一个元素，必须把后面的所有元素都往前挪一个位置，填补空缺。
  这种大量的数据移动 (data movements) 在最坏情况下需要挪动 $N$ 个元素，时间复杂度高达 *$O(N)$*。


  == 2. Linked Lists (列表的链表实现)

为了克服数组在插入和删除时需要大量移动数据的缺点，我们引入了链表。

=== 核心思想：非连续存储与指针引路
在链表中，数据不需要在物理内存中挨在一起。每个数据元素被包装成一个**节点 (Node)**，节点包含两部分：
1. *Data (数据本身)*
2. *Pointer/Next (指向下一个节点内存地址的指针)*

#table(
  columns: (1fr, 1fr, 1fr),
  align: center,
  [*Address (物理地址)*], [*Data (数据)*], [*Pointer (下一节点地址)*],
  [`0010`], [SUN], [`1011`],
  [`0011`], [QIAN], [`0010`],
  [`0110`], [*ZHAO*], [`0011`],
  [`1011`], [LI], [`NULL (空)`]
)
*逻辑顺序*：通过头指针 `ptr = 0110` 找到 `ZHAO` -> 顺着指针 `0011` 找到 `QIAN` -> 顺着 `0010` 找到 `SUN` -> 顺着 `1011` 找到 `LI` -> 遇到 `NULL`，链表结束。

---

=== C 语言中的链表初始化与操作

#block(fill: luma(240), inset: 10pt, radius: 4pt)[
  ```c
  /* 1. 定义节点结构体 (Initialization) */
  typedef struct list_node *list_ptr; // 定义一个指向节点的指针类型
  typedef struct list_node {
      char data[4];   // 存储数据
      list_ptr next;  // 存储下一个节点的地址
  };
  list_ptr ptr;       // 声明头指针
  ```
]


#block(fill: luma(240), inset: 10pt, radius: 4pt)[
```C
/* 2. 动态分配内存并链接 'ZHAO' 和 'QIAN' */
list_ptr N1, N2;

// 使用上一节学过的 malloc 在堆内存中动态申请两个节点的空间
N1 = (list_ptr)malloc(sizeof(struct list_node));
N2 = (list_ptr)malloc(sizeof(struct list_node));

// 赋值数据 (注: 幻灯片中 N1->data = 'ZHAO' 为伪代码，C语言实战中需用 strcpy)
N1->data = "ZHAO"; 
N2->data = "QIAN";

// 建立链接关系
N1->next = N2;   // 让 ZHAO 的 next 指针指向 QIAN
N2->next = NULL; // QIAN 是目前的最后一个节点，指向 NULL

// 头指针指向第一个节点
ptr = N1;        
```
]


= § 3 The Polynomial ADT (多项式抽象数据类型)

将数学中的多项式转化为计算机可以处理的抽象数据类型。

== 1. Objects (数据对象)
在数学中，多项式的标准形式是 $P(x) = a_1 x^{e_1} + ... + a_n x^{e_n}$。
要在计算机中表示它，我们不需要存储变量 $x$ 或是加号 `+`，只需提取出最核心的信息即可。每一个项都可以浓缩为一个**有序对 (ordered pairs)**：$<e_i, a_i>$。
- *$a_i$ (coefficient)*：**系数**。
- *$e_i$ (exponent)*：**指数**。
- *限制条件*：指数 $e_i$ 必须是非负整数。

> *例子*：对于多项式 $P(x) = 5x^2 + 3x + 1$，在计算机眼中，它的对象集合就是 `(<2, 5>, <1, 3>, <0, 1>)`。

== 2. Operations (基本操作规范)
明确了多项式是怎么构成的之后，我们需要定义可以对它进行哪些数学运算操作：
- *Finding degree*：求多项式的度（即找出所有项中最大的指数 $max{e_i}$）。
- *Addition*：两个多项式相加。
- *Subtraction*：两个多项式相减。
- *Multiplication*：两个多项式相乘。
- *Differentiation*：对多项式求导。

=== 多项式的 C 语言链表实现 (代码示例)

为了节省内存并灵活操作，我们使用单向链表，并将各项按**指数降序**排列。

#block(fill: luma(240), inset: 10pt, radius: 4pt)[
  ```c
  /* 1. 基础数据结构定义 */
  typedef struct PolyNode *Polynomial;
  struct PolyNode {
      int coef;       // coefficient (系数)
      int expon;      // exponent (指数)
      Polynomial next; // 指向下一项的指针
  };
  ```
]
==== 操作 1：求多项式的度 (Finding Degree)
由于我们的链表已经按指数降序排列，所以最高次项一定在链表的第一个节点。这使得求度数的时间复杂度直接降为 $O(1)$。

#block(fill: luma(240), inset: 10pt, radius: 4pt)[
  ```c
  int FindDegree(Polynomial P) {
      if (P == NULL) return 0; // 空多项式度为0
      return P->expon;         // 第一个节点的指数就是最高次幂
  }
  ```
]
==== 操作 2：多项式相加 (Addition) -  最经典考点加法的核心逻辑是“双指针合并”：两个指针分别在两个多项式链表上移动，比较指数大小。谁的指数大，谁就先接入结果链表；如果指数一样大，就把系数相加。
#block(fill: luma(240), inset: 10pt, radius: 4pt)[
  ```c
  CPolynomial Add(Polynomial P1, Polynomial P2) {
    // 假设我们有一个创建新节点的辅助函数 Attach() 和一个虚拟头节点 dummyHead
    
    struct PolyNode dummyHead; 
    Polynomial tail = &dummyHead;
    dummyHead.next = NULL;

    while (P1 != NULL && P2 != NULL) {
        if (P1->expon > P2->expon) {
            Attach(P1->coef, P1->expon, &tail); // 将 P1 接到尾部
            P1 = P1->next;
        } 
        else if (P1->expon < P2->expon) {
            Attach(P2->coef, P2->expon, &tail); // 将 P2 接到尾部
            P2 = P2->next;
        } 
        else { // 指数相等，系数相加
            int sum = P1->coef + P2->coef;
            if (sum != 0) { // 只有相加不为0的项才保留
                Attach(sum, P1->expon, &tail);
            }
            P1 = P1->next;
            P2 = P2->next;
        }
    }
    
    // 把 P1 或 P2 中还没遍历完的剩余长尾巴直接接在最后
    // (这里为了代码简洁省略了具体的循环接入过程)
    
    return dummyHead.next; // 返回真正的结果链表头
}
```
]
==== 操作 3：对多项式求导 (Differentiation)根据微积分法则：$(c x^e)' = (c times e) x^{e-1}$。遍历链表，对每一项执行这个数学公式即可。
#block(fill: luma(240), inset: 10pt, radius: 4pt)[
  ```c
  CPolynomial Differentiate(Polynomial P) {
    struct PolyNode dummyHead;
    Polynomial tail = &dummyHead;
    dummyHead.next = NULL;

    while (P != NULL) {
        if (P->expon > 0) { 
            // 常数项 (指数为0) 求导后消失，所以只处理指数大于0的项
            int newCoef = P->coef * P->expon;
            int newExpon = P->expon - 1;
            Attach(newCoef, newExpon, &tail);
        }
        P = P->next;
    }
    return dummyHead.next;
}
```
]


这张图片在一个新章节（Multilists 多重链表）的开头，抛出了一个现实中常见的“多对多”关系问题，并且非常生动地给出了一个反面教材（如那个醒目的倒竖大拇指所示）。

它在教你：在面对大量且稀疏的数据时，千万不要用简单的二维数组！

我为您将这个概念和它背后的（幻灯片没写出来的）潜台词整理成了 Typst 格式笔记：

Code snippet
= § 4 Multilists (多重链表)

在处理复杂的网络状数据关系（例如“多对多”关系）时，我们需要引入比单链表更复杂的结构。

== 【Example】学生选课系统的经典问题
- *背景*：假设学校有 40,000 名学生 (Students) 和 2,500 门课程 (Courses)。
- *业务需求*：
  1. 查询课程：打印出某门课程的所有选课学生名单。
  2. 查询学生：打印出某个学生注册的所有课程列表。

---

== 【Representation 1】二维数组实现 (反面教材 👎)

初学者最容易想到的暴力解法，是建立一个巨大的二维表格（矩阵）：
#block(fill: luma(240), inset: 10pt, radius: 4pt)[
  ```c
  int Array[40000][2500];
  ```
]
逻辑规则：
$ "Array"[i][j] = cases(
1 & text("如果学生") i text("选了课程") j,
0 & text("否则 (未选)")
) $


这种设计在真实的工程应用中是灾难性的，原因有两点：

极度浪费内存 (稀疏矩阵)
数组的总大小是 40,000$times$2,500=100,000,000 个整数。假设一个 int 占 4 字节，光是存这个表就需要约 400 MB 的连续内存。
更致命的是，一个学生一学期通常只选 5~10 门课。这意味着这个庞大矩阵中 99.6% 以上的格子全都是 0。

== 【Representation 2】 十字链表实现 (Cross Linked List) - 👍 完美方案

为了彻底解决二维数组“极度浪费空间”和“查询极慢”的问题，数据结构设计出了“十字链表”。它像织网一样，用横纵两条线把散落的数据精准地串联起来。

#align(center,image("fds_pic/multilianbiao.png",width: 50%))

=== 1. 结构拆解
图中展示了一个小型的学生选课模型（4 门课 C1-C4，5 个学生 S1-S5）。
- *头节点阵列 (Headers)*：
  - 左侧蓝色的 `C1` ~ `C4` 是课程的表头数组。
  - 上方绿色的 `S1` ~ `S5` 是学生的表头数组。
- *数据节点 (Nodes)*：图中间那些绿蓝相间的方块。
  - **核心精髓**：只有当某个学生真正选了某门课时，才会在交叉点创建一个实体节点。没选课的空白区域，在内存中是不存在的.
- *十字指针 (Pointers)*：每个数据节点都有两个方向的指针：
  - **横向指针（蓝色箭头）**：指向下一个选了**同一门课**的节点。顺着它走，就能查出这门课的点名表。
  - **纵向指针（绿色箭头）**：指向该学生选的**下一门课**的节点。顺着它走，就能查出这个学生的专属课表。

=== 2. 模拟业务查询 (为什么它这么快？)
- *场景 A：打印 C1 课程的名单*
  不再需要像二维数组那样盲目扫描 40,000 个学生。我们直接找到左侧的 `C1` 头节点，顺着蓝线向右遍历：
  `C1 -> 遇到节点(属于S1) -> 遇到节点(属于S3) -> 遇到节点(属于S4) -> 绕回C1结束`。
  耗时仅与**实际选课人数**相关。

- *场景 B：打印 S1 学生的所有课程*
  直接找到上方的 `S1` 头节点，顺着绿线向下遍历：
  `S1 -> 遇到节点(属于C1) -> 遇到节点(属于C3) -> 绕回S1结束`。
  耗时仅与**该学生实际选的课时数**相关！

=== 3. 优缺点总结
- *优点*：彻底消灭了无用的空数据存储，空间复杂度大幅降低；两种维度的查询（查课、查人）都极其高效。
- *缺点*：节点的插入和删除操作比较复杂，因为每次变动都需要同时维护横向和纵向两根“线”不被弄断（指针操作极其繁琐，容易产生 Bug）。

== § 5 Cursor Implementation of Linked Lists (链表的游标实现)

=== 1. 核心思想：用数组模拟内存与指针
如果语言没有指针，我们就用一个全局的**结构体数组 (Array of Structures)** 来模拟计算机的整块内存。这块数组被称为 `CursorSpace`。

在这个数组中，每个元素包含两部分：
- *Element (数据)*：存放真实的数据。
- *Next (游标)*：存放下一个节点在数组中的**下标 (Index)**，用来代替真实的内存地址指针。约定 `0` 代表 `NULL`。

=== 2. 模拟内存管理 (自己造轮子)
为了让这个数组像真正的堆内存一样工作，我们需要自己模拟 `malloc` (分配内存) 和 `free` (释放内存) 的操作。

*初始化状态*：
一开始，我们将整个数组串成一个巨大的“空闲备用链表 (Freelist)”。规定数组的第 `0` 个元素 `CursorSpace[0]` 作为这个空闲链表的**表头**。
初始时：`0 -> 1 -> 2 -> ... -> S-1 -> 0`。

==== 模拟 malloc：从空闲链表中取出一个节点
当我们需要新节点时，就从 `CursorSpace[0]` 后面的第一个空闲节点“摘”下来。
#block(fill: luma(240), inset: 10pt, radius: 4pt)[
  ```c
  // 想要一个新节点 p
  p = CursorSpace[0].Next; 
  // 让空闲链表的表头指向下一个空闲节点（把 p 移出空闲队伍）
  CursorSpace[0].Next = CursorSpace[p].Next;
  ```
]

==== 模拟 free：将废弃的节点还给空闲链表
当我们不用节点 p 时，不是真把它删了，而是把它“插回”到空闲链表的头部，留着下次再用。
#block(fill: luma(240), inset: 10pt, radius: 4pt)[

```c
// 释放节点 p
// 1. 让 p 指向目前的第一个空闲节点
CursorSpace[p].Next = CursorSpace[0].Next; 
// 2. 让空闲表头指向 p (把 p 插回空闲队伍的前排)
CursorSpace[0].Next = p;
```
]

=== 3. 游标实现的优势

Note: The cursor implementation is usually significantly faster because of the lack of memory management routines.
速度极快。在操作系统中，真正的 malloc 和 free 涉及到复杂的系统调用，是很耗时的。而游标实现是在我们预先申请好的一块连续数组上玩“下标挪动”的游戏，纯内存操作，速度非常快。这种技巧在做算法竞赛 (ACM) 或者编写对性能要求极高的底层引擎时非常常见（常被称为“静态链表”）。

