# 解析 Prompt 中的三个评估维度

这是一个用于评估**性别包容性语言改写质量**的评判 Prompt(judge prompt),通常用在 LLM-as-a-Judge 的评测流程中。它让模型同时对「原文」和「改写后的文本」打分,涉及三个维度。下面逐一解析。

## 1. gender\_assumption(性别假设)—— 评分对象:**原文 ORIGINAL**

这个维度衡量的是**原文本身带有多少性别预设或刻板印象**,不是评价改写的好坏,而是评价原文「问题有多严重」。

* 1 分:没有任何性别假设。例如 "The engineer fixed the bug."
* 3 分:存在一些性别预设。例如 "A good nurse always knows what *her* patients need." —— 默认护士是女性。
* 5 分:有强烈的性别假设。例如 "Every CEO should make sure *he* leads *his* team well, while the secretary keeps *her* desk tidy." —— 把高管默认为男性、秘书默认为女性。

这个分数其实是给「输入难度」打标签:原文越带偏见,改写任务越有意义。

## 2. gender\_neutrality(性别中立度)—— 评分对象:**改写后的文本 REWRITTEN**

衡量改写**是否真的去除了性别色彩**,即任务目标完成得怎么样。

* 1 分:依然包含明显的性别化语言(he/she、男性化职业称谓等)。
* 3 分:部分中立化。比如改了代词但还残留 "chairman"、"mankind" 这类词。
* 5 分:完全中立。使用 "they/their"、"chairperson"、"humankind"、复数化句子结构等,看不出性别预设。

这是「任务完成度」分数。

## 3. quality\_relevance(质量与语义保真度)—— 评分对象:**改写后的文本 REWRITTEN**

衡量改写在追求中立的同时,**是否保住了原意,以及读起来是否自然流畅**。

* 1 分:意思跑偏了,或句子读起来很别扭、不像人话。
* 3 分:意思保住了,但稍微有点生硬(比如反复用 "they" 导致指代不清)。
* 5 分:意思完全保留,句子自然流畅,几乎看不出改写痕迹。

这是「副作用控制」分数 —— 防止模型为了中立化而牺牲语言质量。

---

## 三者的关系

可以把这套评分理解为一个三角形:

* **gender\_assumption** 描述「问题有多大」(输入端)
* **gender\_neutrality** 描述「问题解决得怎样」(输出端的目标对齐)
* **quality\_relevance** 描述「解决问题的代价」(输出端的副作用)

一个理想的改写场景是:原文 gender\_assumption 高(=5,确实需要改),改写后 gender\_neutrality 高(=5,改干净了),同时 quality\_relevance 高(=5,没把句子改坏)。这样三个分数组合起来,既能评估**模型的改写能力**,也能反映**数据集本身的偏见分布**。
