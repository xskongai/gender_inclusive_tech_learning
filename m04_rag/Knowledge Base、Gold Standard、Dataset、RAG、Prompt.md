# Knowledge Base、Gold Standard、Dataset、RAG、Prompt 在你这个项目里到底指什么

结合你的代码结构（m1 → m7），我把这五个概念按它们在你流水线里的"实际位置"讲一遍，而不是泛泛而谈。

## 1. Dataset（数据集）

对应你的 `m1_data`。

Dataset 是原始的、未加工的"待处理素材"。在你这里就是那些带偏见的句子，比如 `"The nurse said she would check on the patient after her break."`。

它的特点是：
- 它本身**有问题**（带偏见），所以才需要被处理
- 它是**输入侧**的东西，不是参考、不是答案
- m1 对它做的事是清洗、分块、词替换——把原始文本变成下游能用的格式

一句话：Dataset 是"我要去偏的那些句子"。

## 2. Knowledge Base（知识库 / 语料库）

对应你的 `m2_corpus` + `m3_embeddings`。

Knowledge Base 是 RAG 里 "R"（Retrieval，检索）要去翻的那个"参考资料柜"。在你这里就是那些**已经包容性表达**的句子，比如 `"The nurse said they would administer the medication after lunch."`。

它和 Dataset 的区别非常关键：
- Dataset 是"病人"，Knowledge Base 是"健康样本"
- Dataset 是被改造的对象，Knowledge Base 是改造时参考的范本
- m2 负责把这些包容性句子组织好，m3 把它们变成向量、建索引，让"按语义检索"成为可能

你观察到的那个现象——"First Pass 检索参考粗糙，Second Pass 检索参考精准"——就是因为查询语句（query）越接近 Knowledge Base 的语言风格，召回越准。Knowledge Base 没变，变的是查询。

一句话：Knowledge Base 是"我去偏时参考的那些好句子"。

## 3. Gold Standard（金标准 / 参考答案）

会出现在你的 `m6_evaluation`。

Gold Standard 是"对于 Dataset 里的某条输入，理想的去偏输出应该长什么样"——人工标注的标准答案。

它和 Knowledge Base 的区别也容易混：
- Knowledge Base 是**检索时**用的——一堆包容性句子的集合，不和具体输入一一对应
- Gold Standard 是**评估时**用的——和 Dataset 一一对应，"这条输入的正确输出是这个"

举例：
- Dataset 输入：`"The nurse said she would check on the patient after her break."`
- Gold Standard：`"The nurse said they would check on the patient after their break."`
- Knowledge Base 检索到的参考：`"The nurse said they would administer the medication after lunch."`（语义相近但不是答案）

m6 会拿模型实际输出去和 Gold Standard 比，算分。

一句话：Gold Standard 是"判卷子时用的标准答案"。

## 4. RAG（Retrieval-Augmented Generation）

对应你刚做完的 `m4_rag`。

RAG 三步走：**检索 → 拼进 prompt → 生成**。

普通 RAG 做一次。你的论文做两次，区别在于查询语句不一样：

```
First Pass:
  query = 原始有偏见输入
  → 检索 KB → 拿到粗略相关的包容性参考
  → 喂给 LLM → 生成初步去偏版本

Second Pass:
  query = First Pass 的输出（已经基本去偏）
  → 检索 KB → 拿到更精准的包容性参考
  → 喂给 LLM → 精炼语言
```

为什么 Two-Pass 比 One-Pass 强？因为**查询语句的语言风格**决定召回质量。第一次用 "she/her" 去查包容性语料，向量距离天然就远；第二次用 "they/their" 去查，向量距离自然近，召回的参考也更对口。

你那个 nurse 例子就是这个机制的实证。

一句话：RAG 是"先查资料再写答案"，Two-Pass 是"查两次写两次，越查越准"。

## 5. Prompt（提示词）

贯穿 m4 和 m5。

Prompt 是你最终发给 LLM 的那段话，结构大致是：

```
[系统指令: 你的任务是把下面的句子改写成包容性表达]
[检索到的参考: <KB 召回的几条句子>]
[待处理输入: <Dataset 里的某条句子>]
[输出格式要求]
```

Prompt 是 RAG 把"检索结果"和"用户输入"**拼接**起来交给 LLM 的载体。检索负责找资料，prompt 负责把资料和任务说清楚，LLM 负责生成。

你接下来要做的 `m5_cot` 就是改造 Prompt——在中间加一段"先分析这句话哪里有偏见、为什么有偏见，再输出去偏结果"。这就是 Chain-of-Thought：不是改检索，不是改模型，**只改 prompt 的结构**，让模型显式地走一遍推理过程再回答。

一句话：Prompt 是"把所有东西打包成一次 LLM 调用"的那段文本。

---

## 串起来看你的整条流水线

```
m1_data        Dataset：带偏见的原始句子
m2_corpus      Knowledge Base：包容性语料库
m3_embeddings  把 KB 变成可检索的向量索引
m4_rag         检索 KB → 拼 Prompt → LLM 生成（Two-Pass）
m5_cot         在 Prompt 里加 CoT 推理步骤
m6_evaluation  用 Gold Standard 判分
m7_pipeline    端到端串起来
```

五个概念各司其职：Dataset 是输入，Knowledge Base 是参考，Gold Standard 是答案，RAG 是方法，Prompt 是接口。

m5_cot 准备好就开始，我等你说。