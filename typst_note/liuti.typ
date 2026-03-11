#import "@preview/typsidian:0.0.3": *

#show: typsidian.with(
  title: "", 
  course: "工程流体力学",
  author: "彧君"
)

#set text(font: ("Inter", "KaiTi"), lang: "zh")
// #make-title()

#align(center)[
  #block(inset: 2em)[
    #text(weight: "bold", size: 2.5em)[工程流体力学] \
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
= 绪论

大量分子

热运动

分子作用力



流体具有可压缩性和热膨胀性，气体更为明显

== 流体质点

以*流体质点*作为研究对象，没有空间尺寸，但是有物理量，并且是时间和空间的函数。

=== *流体的相关物理量*

  - 密度$ rho = (d m) / (d V) $
  - 比体积$ v = V / m = 1 / rho $
  - 相对密度$ d = rho / rho_"ref" $$rho_"ref"$代表4℃时蒸馏水的密度
=== 流体的膨胀性和压缩性

相比于液体来说，气体具有状态方程：

$ p V=m R_g T $
除了方程表示法之外，还有系数表示法

1.膨胀系数$ alpha_v = 1/V (d V) / (d T) |_p $
可以理解为相同压强变化下，单位温度的相对体积变化量

对气体而言，其等压膨胀系数可以通过气体状态方程推导出：$ alpha_v = 1/T $
2.体积压缩率
$ kappa = - 1/V (d V) / (d p) |_T $
对气体而言，其等温压缩率可以通过气体状态方程推导出
$ kappa = 1/p $
3.体积模量
$ K = 1 / kappa = - V (d p) / (d V) |_T $
可以类比为弹簧的弹性系数

#box(theme: "example", title: "Example", [
 
  如果液体中混有不溶解的气体，弹性模量将有很大的降低。设体积为 $V_m$ 的混气油液中，如果气体的体积为 $V_g$，则纯油液的体积 $V_l = V_m - V_g$。当压强增加 $Delta p$ 时，混气油液的体积减小 $Delta V_m$，应为气体体积减小 $Delta V_g$ 和纯油体积减小 $Delta V_l$ 的总和，即
  $ Delta V_m = Delta V_g + Delta V_l $

  因为体积弹性模量为：$K_m = (-V_m Delta p) / (Delta V_m)$，$K_g = (-V_g Delta p) / (Delta V_g)$ 及 $K_l = (-V_l Delta p) / (Delta V_l)$，代入上式得
  $ (V_m Delta p) / K_m = (V_g Delta p) / K_g + (V_l Delta p) / K_l $

  或
  $ 1 / K_m = V_g / V_m (1 / K_g) + V_l / V_m (1 / K_l) = V_g / V_m (1 / K_g) + (1 - V_g / V_m) (1 / K_l) $

  例如某油液（$K_l = 1.8 times 10^3 "MPa"$），混有一定的气体，作用 $10 "MPa"$ 压强后油液的温度不变，则 $K_g = 10 "MPa"$，这样，混气油液的体积弹性模量 $K_m$ 为
  $ 1 / K_m = (V_g / V_m) / 10 + (1 - V_g / V_m) / (1.8 times 10^3) $

  由此可以计算出不同混入气体量时的体积弹性模量。上例说明在一定压强下，油液夹带 $1%$ 气体时弹性模量降为纯油的 $35.6%$，夹带 $4%$ 气体时则仅为纯油液的 $12.2%$。由此可见，在需要大体积弹性模量的场合，必需严格排除油液中夹带的气体。实际计算中常用 $K = 7000 ~ 10000 "MPa"$。
])

压缩性

不可压缩流体的特点是：

$ rho = "Constant" $

可压缩流体：如子弹在高速运动的时候，周围空气会被压缩
== 流体的粘性
原因：
- 分子之间吸引力
- 不规则热运动
- 不断的动量交换
=== 牛顿内摩擦定律
#align(center, image("material_pic/newton.png", width: 70%))
流体对上板摩擦力大小：
$ F = mu v_0/delta A $
可以据此得到切应力：
$ tau = F/A = mu v_0/delta $
实际上，$v_0/delta$指的是速度梯度，公式写得更准确一点：
$ tau = plus.minus mu (d v)/ (d y) $


#box(theme: "example", title: "Example", [

  #align(center, image("material_pic/liti2.png", width: 50%))
 
  在相距 $h = 0.06 "m"$ 的两个固定平行平板中间放置另一块薄板，在薄板的上下分别放有不同黏度的油，并且一种油的黏度是另一种油的黏度的 2 倍。当薄板以匀速 $v = 0.3 "m/s"$ 被拖动时，每平方米受合力 $F = 29 "N"$，求两种油的黏度各是多少？

  *解：* 设薄板上层油的黏度为 $mu$，则下层为 $2mu$，并假定缝隙中的速度按线性分布，薄板与流体接触的面积为 $A$。

  由牛顿内摩擦定律可知，上部流体对板的阻碍力为
  $ F_1 = mu A (d v) / (d n) = mu A v / (h / 2) $
  其作用方向与薄板的运动方向相反。

  下部流体对板的作用力为
  $ F_2 = 2 mu A (d v) / (d n) = 2 mu A v / (h / 2) $
  其作用方向仍与薄板的运动方向相反。

  薄板匀速运动，受力处于平衡状态，必有
  $ F = F_1 + F_2 $
  即
  $ mu A v / (h / 2) + 2 mu A v / (h / 2) = F $
  或
  $ mu = h / (6 v) times F / A $

  代入相关数据得 $mu = 0.97 "Pa" dot "s"$，这是薄板上层油的黏度。薄板下层油的黏度 $2 mu = 1.94 "Pa" dot "s"$。
])

也适用于速度梯度非线性变化的情况，$plus.minus$是为了保证$tau$一直是正值。
#align(center,image("material_pic/feixianxing.png",width: 50%))


#box(theme: "example", title: "Example", [

  #align(center, image("material_pic/liti3.png", width: 30%))
 
  旋转式粘度计由内外圆筒构成，它们的半径各为 $R_1$ 及 $R_2$，内圆筒用扭力弹簧固定，外圆筒以等角速度 $omega$ 旋转，两圆筒的径向间隙为 $delta_1$，底面间隙为 $delta_2$，内外圆筒间充入被测液体至 $h$ 高度，如果扭力弹簧上扭矩为 $T$，求被测液体的粘度 $mu$。

  *解：* 因为间隙 $delta_1$ 及 $delta_2$ 均很小，间隙中速度成线性分布，所以径向间隙中速度梯度 $ (d u) / (d r) = (omega R_2) / delta_1 $，剪切应力 $tau_1$ 为
  $ tau_1 = mu (d u) / (d r) = mu (omega R_2) / delta_1 $

  由此，内圆筒侧面上剪切应力引起的扭矩 $T_1$ 为
  $ T_1 = A tau_1 R_1 = (2 pi R_1 h) dot (mu (omega R_2) / delta_1) R_1 = 2 pi R_1^2 (omega R_2) / delta_1 mu h $

  内圆筒底部的剪切应力
  $ tau_2 = mu (d u) / (d z) = mu (omega R) / delta_2 $

  式中，$R$ 为变量，由此引起的扭矩 $T_2$ 为
  $ T_2 = integral d T_2 = integral tau_2 R d A = integral.double mu (omega R^2) / delta_2 R d R d theta $

  即
  $ T_2 = mu omega / delta_2 integral_0^(2 pi) d theta integral_0^(R_1) R^3 d R = pi / (2 delta_2) mu omega R_1^4 $

  总扭矩 $T$ 为
  $ T = T_1 + T_2 = (2 pi R_1^2 R_2 h omega mu) / delta_1 + (pi R_1^4 omega mu) / (2 delta_2) $

])

- 牛顿流体
切应力与速度梯度成正比（$tau-(d v)/(d y)$线过原点）
- 非牛顿流体
#align(center,image("material_pic/feinewton.png",width: 70%))
=== 流体的粘度
当流体运动时，粘度才会体现出来

动力粘度
$ mu = tau / ((d u) / (d y)) $
运动粘度
$ nu = mu/rho $  
个人感觉可以类比为动量和速度的关系，这一点也可以从单位上看出来。


