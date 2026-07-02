---
title: Signals & Systems CH1-CH4 Midterm Cheatsheet
subtitle: 手写稿电子转写示例：FS / CTFT
author: Example Author
theme: tech-minimal
document_type: article
layout: cheatsheet
---

:::: {.cheatsheet-grid columns="4" gap="compact"}

# 一、复数与三角函数 {.manual-number}

## 1. 模、共轭、复值、辐角 {.manual-number}

- $z=a+bj=r(\cos\theta+j\sin\theta)$.
- $|z|=\sqrt{a^2+b^2}$；$z^\ast=(a-bj)$，共轭.
- $z\cdot z^\ast=|z|^2$；$-z=-a-bj$.
- $\theta=\arctan(b/a)$.
- $1/j=-j$.

## 2. 欧拉公式；逆欧拉公式 {.manual-number}

- $e^{j\theta}=\cos\theta+j\sin\theta$.
- $\cos\theta=\frac{1}{2}(e^{j\theta}+e^{-j\theta})$.
- $\sin\theta=\frac{1}{2j}(e^{j\theta}-e^{-j\theta})$.

::: {.cheatsheet-cell type="keypoint" title="别忘了！" priority="high"}
$\sin\theta$ 的逆欧拉公式系数是 $1/(2j)$.
:::

**3.**

- $A e^{j(wt+\varphi)}=A\cos(wt+\varphi)+jA\sin(wt+\varphi)$.
- $A$：振幅；$|e^{j(wt+\varphi)}|=1$.
- $w$：角频率；$\varphi$：初相位.

**4.**

- $z=|z|e^{j\theta}$，振幅 + 相位.
- $\tan\varphi=b/a$.

**5.**

- $e^{jk\pi}=-1$ when $k$ odd；$e^{jk\pi}=1$ when $k$ even.

**6.**

- $a\sin\eta+b\sin\theta=\sqrt{a^2+b^2}\sin(a+\varphi)$. `[待辨认：最后一项原稿较模糊]`

# 二、CH1 基本信号 {.manual-number}

## 1. 能量 & 功率 {.manual-number}

**C.T.**

- $$E_\infty=\int_{-\infty}^{+\infty}|x(t)|^2dt$$
- $$P_\infty=\lim_{T\to\infty}\frac{1}{2T}\int_{-T}^{T}|x(t)|^2dt$$

**D.T.**

- $$E_\infty=\sum_{n=-\infty}^{+\infty}|x[n]|^2$$
- $$P_\infty=\lim_{N\to\infty}\frac{1}{2N+1}\sum_{k=-N}^{N}|x[n]|^2$$ `[原稿写法保留，求和指标疑似应为 k]`

- Finite Energy: $E<\infty,\ P=0$.
- Finite Power: $E=\infty,\ P<\infty$.

## 2. 信号的时域变换 {.manual-number}

- $x(t)\to x(at+\beta)$.
- 标准顺序：
  1. Time shifting：$x(t)\to x(t+\beta)$.
  2. Time Scaling：$x(t+\beta)\to x(|a|t+\beta)$.
  3. Time Reversing：$x(|a|t+\beta)\to x(at+\beta)$.
- $|a|>1$：压缩；$|a|<1$：拉伸.
- scaling 只对各 $t$ 取值有影响.
- 对 D.T. Signal，压缩可能丢失等等.

**周期性**

- $x(t)=x(t+T)$；$x[n]=x[n+N]$.
- fundamental period $T_0$（不一定存在）.
- fundamental frequency $w_0=2\pi/T_0$.
- C.T. $\to$ D.T. 不一定保持周期性；只有 $T_0/T_s\in\mathbf{Q}$ 时不转变.
- 两个 C.T. periodic signal 只有在 $T_1/T_2\in\mathbf{Q}$ 时，其和才有公共周期 LCM.
- 离散周期信号：`没这个问题`. `[原稿原句近似转写]`

## 3. 信号的性质 {.manual-number}

**① 奇偶性**

- $x(t)=x_e(t)+x_o(t)$.
- $x_e(t)=\frac{x(t)+x(-t)}{2}$.
- $x_o(t)=\frac{x(t)-x(-t)}{2}$.

**③ “$\delta$” 和 “$u$”**

- $\delta[n]=u[n]-u[n-1]$.
- $$u[n]=\sum_{m=-\infty}^{n}\delta[m]=\sum_{k=0}^{\infty}\delta[n-k]$$
- 采样特性：
  $x[n]\delta[n-n_0]=x[n_0]\delta[n-n_0]$.
- $x(t)\delta(t-t_0)=x(t_0)\delta(t-t_0)$.

## 4. 系统的性质 {.manual-number}

**① 记忆性**

- memoryless：只与当前 input 依存.
- not memoryless：当前 + 过去/未来 input 依存.

**② 可逆性 (invertible)**

- input 不同 $\to$ output 不同.

**③ 因果性 (causal)**

- $y(t)=x(-t)$：$\times$.
- $y(t)=x(t)\cos(t+1)$：OK.

**④ 时不变 (Time-invariant)**

- $x(t)\to y(t)$ 可否 $x(t-t_0)\to y(t-t_0)$.
- “先平移和变换” = “先变换后平移”.

**⑤ 稳定性 (Stability)**

- Bounded in, bounded out.
- $|x|<B$，$|y|<B'$.
- `[原稿蓝字]` 不包括 $\delta(t)$.

**⑨ 单位阶跃响应**

- $s[n]=\sum_{k=-\infty}^{n}h[k]$.
- $h[n]=s[n]-s[n-1]$.

# 三、LTI Systems & Convolution {.manual-number}

## 1. 单位冲激响应 (Unit Impulse Response) {.manual-number}

- $h[n]:\ y[n]=T\{x[n]\}\Rightarrow h[n]=T\{\delta[n]\}$.
- $h(t):\ y(t)=T\{x(t)\}\Rightarrow h(t)=T\{\delta(t)\}$.

## 2. 卷积 (Convolution) {.manual-number}

- $$x[n]\ast h[n]=\sum_{k=-\infty}^{+\infty}x[k]h[n-k]$$（卷积和，Conv. Sum）
- 两种 Method：
  1. $n,k$ 为变量：先找 $k$ 的范围（$x[k]$），再找 $n-k$ 的范围（$h[n-k]$），得出 $n$ 的范围，代入求值。
  2. $n,k$ 为变量：$x[n]\to x[k]$，$h[n]\to h[k]$，翻转平移 $h[n-k]$，相乘相加。
- $$x(t)\ast h(t)=\int_{-\infty}^{+\infty}x(\tau)h(t-\tau)d\tau$$

**③ 卷积的性质**

- 交换律：$x\ast h=h\ast x$.
- 分配律：$x\ast(h_1+h_2)=x\ast h_1+x\ast h_2$.
- 结合律：$(x\ast h_1)\ast h_2=x\ast(h_1\ast h_2)$.

**④ 常用卷积公式**

- $x(t)\ast\delta(t-t_0)=x(t-t_0)$.
- $x[n]\ast\delta[n-n_0]=x[n-n_0]$.
- $x(t)\ast u(t)=\int_{-\infty}^{t}x(\tau)d\tau$.
- $x[n]\ast u[n]=\sum_{k=-\infty}^{n}x[k]$.
- $u(t)\ast u(t-t_0)=(t-t_0)u(t-t_0)$.
- $[f(t)\ast g(t-t_0)](t)=[f(t)\ast g(t)](t-t_0)$.
- $[f(at)\ast g(at)](t)=\frac{1}{|a|}(f\ast g)(at)$.
- 如果 $a<0$，为让积分上下限顺序，取负号，因此有绝对值。

**h(t)/h[n] 的系统性质（①–④）**

**① 无记忆性**

- $h[n]=0$ for all $n\ne0$.
- $h(t)=0$ for all $t\ne0$.

**② 可逆性**

- $h_0[n]\ast h_1[n]=\delta[n]$.
- $h_0(t)\ast h_1(t)=\delta(t)$.

**③ 因果性**

- $h[n]=0$ for $n<0$.
- $h(t)=0$ for $t<0$.

**④ 稳定性**

- $$\sum_{k=-\infty}^{+\infty}|h[k]|<\infty$$
- $$\int_{-\infty}^{+\infty}|h(t)|dt<\infty$$
- 其由绝对收敛决定，实质是 Abel Test（收敛，常用）.

::: {.cheatsheet-cell type="example" title="补充：第一页右下（原稿）" priority="medium"}
**1. 模变换定理**

- $z_1=r_1(\cos\theta_1+j\sin\theta_1)$.
- $z_2=r_2(\cos\theta_2+j\sin\theta_2)$.
- $z_1z_2=r_1r_2[\cos(\theta_1+\theta_2)+j\sin(\theta_1+\theta_2)]$.

**2. 信号取 $w_0$**

- 通过找 $T_0$ 来算出；$a_k$ 前不都是基于 $kw_0$ 来算的。

**3. 方波 F.S.**

- $x(t)=1,\ |t|<T_1$；$x(t)=0,\ T_1<|t|<T/2$.
- $a_0=2T_1/T$.
- $$\begin{aligned}a_k&=\frac{e^{jk w_0T_1}-e^{-jk w_0T_1}}{2jk\pi}\\&=\frac{\sin(k w_0T_1)}{k\pi}\end{aligned}$$

**4. Block Diagram**

- $$y(t)=\int_{-\infty}^{t}[b x(\tau)-a y(\tau)]d\tau$$
- $$y(t)=-\frac{1}{a}\frac{dy(t)}{dt}+\frac{b}{a}x(t)$$ `[待辨认：下方第二个 block diagram 未完整转写]`
:::

# 四、Ch3. Fourier Series {.manual-number}

## 1. Eigenfunction {.manual-number}

- C.T.：$e^{st}\stackrel{\mathrm{LTI}}{\to}H(s)e^{st}$，
  $$H(s)=\int_{-\infty}^{+\infty}h(t)e^{-st}dt$$
- D.T.：$z^n\stackrel{\mathrm{LTI}}{\to}H(z)z^n$，
  $$H(z)=\sum_{k}h[k]z^{-k}$$
- $z=\cos\theta+j\sin\theta$.
- $z^n=\cos(n\theta)+j\sin(n\theta)=e^{jn\theta}$.
- 若为有理数 $\Rightarrow$ 周期性（例子）.

## 2. 周期信号内积 {.manual-number}

- $$\begin{aligned}&\langle x_1(t),x_2(t)\rangle\\&=\frac{w_0}{2\pi}\int_{-N_0/w_0}^{N_0/w_0}x_1(t)x_2^\ast(t)dt\end{aligned}$$
- $$\langle x_1[n],x_2[n]\rangle=\frac{1}{N}\sum_{n=0}^{N-1}x_1[n]x_2^\ast[n]$$
- $N\in\mathbf{N}$，有限范围.

## 3. 性质 {.manual-number}

**① 公式**

- 分析：$$a_k=\sum_{n=\langle N\rangle}x[n]e^{-jkn(2\pi/N)}$$
- 综合：$$x[n]=\sum_{k=\langle N\rangle}a_ke^{jkn(2\pi/N)}$$
- $$a_k=\frac{1}{T}\int_Tx(t)e^{-jkw_0t}dt$$
- $$x(t)=\sum_{k=-\infty}^{+\infty}a_ke^{jkw_0t}$$

**② 线性**

- $Ax[n]+By[n]\stackrel{\mathrm{FS}}{\leftrightarrow}Aa_k+Bb_k$.
- $Ax(t)+By(t)\stackrel{\mathrm{FS}}{\leftrightarrow}Aa_k+Bb_k$.

**③ 时移**

- $x[n-n_0]\stackrel{\mathrm{FS}}{\leftrightarrow}e^{-j(2\pi/N)kn_0}a_k$.
- $x(t-t_0)\stackrel{\mathrm{FS}}{\leftrightarrow}e^{-jkw_0t_0}a_k$.

**④ 频移**

- $x[n]e^{j(2\pi/N)nM}\stackrel{\mathrm{FS}}{\leftrightarrow}a_{k-M}$.
- $x(t)e^{jMw_0t}\stackrel{\mathrm{FS}}{\leftrightarrow}a_{k-M}$.

**⑤ 共轭**

- $x^\ast[n]\stackrel{\mathrm{FS}}{\leftrightarrow}a_{-k}^\ast$；$x^\ast(t)\stackrel{\mathrm{FS}}{\leftrightarrow}a_{-k}^\ast$.
- $x(t)$ real $\Rightarrow a_k=a_{-k}^\ast$.
- $x(t)$ real + even $\Rightarrow a_k$ real + even.
- $x(t)$ real + odd $\Rightarrow a_k$ pure imaginary + odd.

**⑥ 时域放缩**

- $x_{(m)}[n]\stackrel{\mathrm{FS}}{\leftrightarrow}\frac{1}{m}a_k$，$x_{(m)}[n]=x[n/m]$ when $n$ 为 $m$ 倍数，otherwise $0$.
- $x(dt)\stackrel{\mathrm{FS}}{\leftrightarrow}a_k$，$w_0'=dw_0$，$T_{\mathrm{new}}=T/d$.

**⑦ 周期卷积**

- $$\sum_{r=\langle N\rangle}x[r]h[n-r]\stackrel{\mathrm{FS}}{\leftrightarrow}Ta_kb_k$$
- $$\int_Tx(\tau)h(t-\tau)d\tau\stackrel{\mathrm{FS}}{\leftrightarrow}Ta_kb_k$$

**⑧ 乘法**

- $$x[n]y[n]\stackrel{\mathrm{FS}}{\leftrightarrow}\sum_{l=\langle N\rangle}a_lb_{k-l}$$
- $$x(t)y(t)\stackrel{\mathrm{FS}}{\leftrightarrow}\sum_{l=-\infty}^{+\infty}a_lb_{k-l}$$

**⑨ 时域反转**

- $x[-n]\stackrel{\mathrm{FS}}{\leftrightarrow}a_{-k}$.
- $x(-t)\stackrel{\mathrm{FS}}{\leftrightarrow}a_{-k}$.

**⑩ 差分/微分**

- $$x[n]-x[n-1]\stackrel{\mathrm{FS}}{\leftrightarrow}(1-e^{-j(2\pi/N)k})a_k$$
- $$\frac{dx(t)}{dt}\stackrel{\mathrm{FS}}{\leftrightarrow}jkw_0a_k$$

**⑪ 前缀和/积分**

- $$\sum_{k=-\infty}^{n}x[k]\stackrel{\mathrm{FS}}{\leftrightarrow}\frac{a_k}{1-e^{-j(2\pi/N)k}}$$
- $$\int_{-\infty}^{t}x(\tau)d\tau\stackrel{\mathrm{FS}}{\leftrightarrow}\frac{a_k}{jkw_0}$$

**⑫ Parseval's Relation**

- $$\frac{1}{N}\sum_{n=\langle N\rangle}|x[n]|^2=\sum_{k=\langle N\rangle}|a_k|^2$$
- $$\frac{1}{T}\int_T|x(t)|^2dt=\sum_{k=-\infty}^{+\infty}|a_k|^2$$

**⑬ 收敛**

- 仅 C.T.，D.T. 是周期区间内有限点即可.
- Case 1：有限能量，$\int|x(t)|dt<\infty\Rightarrow$ 有 FS 但不一定相等.
- Case 2：绝对可积，最大/最小值有限个，周期内不连续点有限且左右极限存在；在跳变点取平均值.

# 五、Ch4. C.T.F.T. {.manual-number}

## 1. 推导 {.manual-number}

- 记 $$\begin{aligned}X(j\omega)&=\lim_{T\to\infty}Ta_k\\&=\lim_{T\to\infty}\int_Tx(t)e^{-jkw_0t}dt\\&=\int_{-\infty}^{+\infty}x(t)e^{-jkw_0t}dt\end{aligned}$$
- $T\to\infty$，$w_0=2\pi/T\to d\omega$.
- $x(t)=\sum_{k=-\infty}^{+\infty}a_ke^{-jkw_0t}$；$T\cdot 1/T$ 项进入积分形式. `[待辨认：原稿推导中部有遮挡]`
- 非周期信号 = $T\to\infty$ 的周期信号.

## 2. 公式 {.manual-number}

- 分析：$$X(j\omega)=\int_{-\infty}^{+\infty}x(t)e^{-j\omega t}dt$$
- 综合：$$x(t)=\frac{1}{2\pi}\int_{-\infty}^{+\infty}X(j\omega)e^{j\omega t}d\omega$$

## 3. 性质 {.manual-number}

- $aX(t)+bY(t)\stackrel{\mathcal F}{\leftrightarrow}aX(j\omega)+bY(j\omega)$.
- $x(t-t_0)\stackrel{\mathcal F}{\leftrightarrow}e^{-j\omega t_0}X(j\omega)$.
- $x^\ast(t)\stackrel{\mathcal F}{\leftrightarrow}X^\ast(-j\omega)$.
- $x(-t)\stackrel{\mathcal F}{\leftrightarrow}X(-j\omega)$.
- $x(at)\stackrel{\mathcal F}{\leftrightarrow}\frac{1}{|a|}X(j\omega/a)$.
- $x(t)\ast h(t)\stackrel{\mathcal F}{\leftrightarrow}H(j\omega)X(j\omega)$.
- $s(t)\cdot p(t)\stackrel{\mathcal F}{\leftrightarrow}\frac{1}{2\pi}[S(j\omega)\ast P(j\omega)]$.
- $\frac{dx(t)}{dt}\stackrel{\mathcal F}{\leftrightarrow}j\omega X(j\omega)$.
- $$\begin{aligned}&\int_{-\infty}^{t}x(\tau)d\tau\\&\stackrel{\mathcal F}{\leftrightarrow}\frac{1}{j\omega}X(j\omega)+\pi X(0)\delta(\omega)\end{aligned}$$
- $x(t)=x_e(t)+x_o(t)$，$\mathcal F\{x(t)\}=\mathcal F\{x_e(t)\}+\mathcal F\{x_o(t)\}$.
- $$\begin{aligned}&\int_{-\infty}^{+\infty}|x(t)|^2dt\\&=\frac{1}{2\pi}\int_{-\infty}^{+\infty}|X(j\omega)|^2d\omega\end{aligned}$$

## 4. 常见信号的 F.T. {.manual-number}

- $e^{-a|t|},\ a>0\stackrel{\mathcal F}{\leftrightarrow}\frac{2a}{a^2+\omega^2}$.
- $e^{-at}u(t),\ a>0\stackrel{\mathcal F}{\leftrightarrow}\frac{1}{a+j\omega}$.
- $\delta(t)\stackrel{\mathcal F}{\leftrightarrow}1$.
- $1\stackrel{\mathcal F}{\leftrightarrow}2\pi\delta(\omega)$.
- $\frac{\sin(Wt)}{\pi t}\stackrel{\mathcal F}{\leftrightarrow}1,\ |\omega|<W$；$0,\ |\omega|>W$.
- $e^{-at}u(t)\stackrel{\mathcal F}{\leftrightarrow}\frac{1}{a+j\omega}$.

**对偶性质**

- $x(t)\stackrel{\mathcal F}{\leftrightarrow}X(j\omega)$.
- $X(t)\stackrel{\mathcal F}{\leftrightarrow}2\pi x(-j\omega)$.
- $\mathrm{Od}\{x(t)\}\stackrel{\mathcal F}{\leftrightarrow}j\mathrm{Im}\{X(j\omega)\}$.
- $e^{-a|t|}\stackrel{\mathcal F}{\leftrightarrow}\frac{2a}{a^2+\omega^2}$，$a=1$ 时 $\frac{2}{1+t^2}\stackrel{\mathcal F}{\leftrightarrow}2\pi e^{-|\omega|}$.

## 5. 周期信号的 F.T. {.manual-number}

- $x(t)=\sum_{k=-\infty}^{+\infty}a_ke^{jkw_0t}$.
- $$X(j\omega)=\sum_{k=-\infty}^{+\infty}2\pi a_k\delta(\omega-kw_0)$$

**e.g. 方波**

- $$\begin{aligned}&X(j\omega)\\&=\sum_{k=-\infty}^{+\infty}\frac{2\pi\sin(kw_0T_1)}{k}\delta(\omega-kw_0)\end{aligned}$$
- $\sin w_0t$：$$X(j\omega)=\frac{\pi}{j}\delta(\omega-w_0)-\frac{\pi}{j}\delta(\omega+w_0)$$
- $\cos w_0t$：$$X(j\omega)=\pi\delta(\omega-w_0)+\pi\delta(\omega+w_0)$$

## 6. 频率响应 {.manual-number}

- $$H(s)=\int_{-\infty}^{+\infty}h(t)e^{-st}dt$$
- $s=j\omega$：$$H(j\omega)=\int_{-\infty}^{+\infty}h(t)e^{-j\omega t}dt$$
- $$H[z]=\sum_{n=-\infty}^{+\infty}h[k]z^{-n}$$ $z=e^{j\omega}$ 时 $$H(e^{j\omega})=\sum_{n=-\infty}^{+\infty}h[n]e^{-j\omega n}$$
- $b_k=a_kH(j\omega)$；$b_k=a_kH(e^{j\omega})$.

::: {.cheatsheet-cell type="note" title="补充：右下原文（原稿蓝字）" priority="medium"}
1. 离散情况下，把 $[-\infty,+\infty]$ 折成概率；永远不漏.
2. 某些情况下，$r$ 可能奇异（e.g. $e^{-at}$）.
3. $a_0$ 和 $a_n(k\ne0)$ 可能有中断区间，要分开讨论 $k$.
4. $$\begin{aligned}&S(j\omega)\ast P(j\omega)\\&=\int_{-\infty}^{+\infty}S(j\theta)P(j\omega-j\theta)d\theta\end{aligned}$$
5. 别忘记代入 $w_0$（e.g. $w_0=\frac{2}{3}\pi$ 等）；有时 F.T. 根号下不能约.
6. 证其性质：用综合公式！
7. $x(t)\stackrel{\mathrm{FS}}{\leftrightarrow}a_k$，$y(t)=\int_{-\infty}^{t}x(t)dt$；$y(t)$ 有 Fourier Series 后有要求：$a_0=0$（否则 $a_0$ 处还有 $+\infty$）.
8. 结果若 $n\ge0$，可用 $u[n]$ 省掉 $n<0$ 的讨论.
9. $u(t)\stackrel{\mathcal F}{\leftrightarrow}\pi\delta(\omega)+\frac{1}{j\omega}$；定义 $Sgn(t)=1,\ t>0$；$Sgn(t)=-1,\ t<0$.
10. $\frac{d\,sgn(t)}{dt}=2\delta(t)$；这个信号 convergence 条件的信号不能直接用定义算. `[待辨认：蓝字原文近似]`
:::
::::
