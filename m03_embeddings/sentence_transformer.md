
# SentenceTransformer 重点讲解

`sentence_transformers` 是一个基于 PyTorch 和 Transformers 的 Python 库,核心功能是把**句子、段落、图像**转换成**稠密向量(embeddings)**,用于语义搜索、聚类、相似度计算等任务。

## 核心思想

传统 BERT 输出的是每个 token 的向量,要表示整句话需要额外处理(比如取 [CLS] 或平均池化),但效果一般。`
SentenceTransformer` 通过**孪生网络(Siamese Network)**结构微调 BERT,让模型直接输出**语义层面可比较的句向量**
——也就是说,语义相近的句子,向量的余弦相似度就高。

## 基本用法

```python
from sentence_transformers import SentenceTransformer

# 加载预训练模型(第一次会自动下载)
model = SentenceTransformer('all-MiniLM-L6-v2')

# 编码句子 → 得到向量
sentences = ["今天天气真好", "外面阳光明媚", "我喜欢吃火锅"]
embeddings = model.encode(sentences)

print(embeddings.shape)  # (3, 384) 每句变成 384 维向量
```

## 几个关键点

**1. 模型选择**
- `all-MiniLM-L6-v2`:轻量快(384 维),英文场景的入门首选
- `all-mpnet-base-v2`:精度更高(768 维),速度慢一些
- `paraphrase-multilingual-MiniLM-L12-v2`:**支持中文等 50+ 语言**,做中文任务用这个
- `BAAI/bge-large-zh-v1.5`:专门针对中文优化,目前中文榜单上表现很强

**2. 计算相似度**

```python
from sentence_transformers import util

emb1 = model.encode("猫在沙发上睡觉")
emb2 = model.encode("一只猫正在沙发上休息")
similarity = util.cos_sim(emb1, emb2)  # 输出接近 1 表示语义相近
```

**3. 常见应用场景**
- **语义搜索**:把文档库全部编码存起来,查询时编码 query,找最相似的(RAG 的核心环节)
- **聚类**:对大量文本分组
- **去重**:找语义重复的内容
- **推荐**:基于内容相似度做匹配

**4. encode() 的实用参数**
- `batch_size=32`:批量大小,影响速度和显存
- `convert_to_tensor=True`:返回 PyTorch tensor 而不是 numpy,适合后续 GPU 运算
- `normalize_embeddings=True`:归一化后,点积就等于余弦相似度,在向量数据库里检索更快
- `show_progress_bar=True`:大批量编码时显示进度条

**5. 和向量数据库配合**

实际项目里基本都是 `SentenceTransformer` + 向量库(FAISS、Milvus、Chroma、Pinecone)的组合:用前者生成向量,用后者存储和做近似最近邻检索(ANN)。

## 一个完整的语义搜索小例子

```python
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')

# 文档库
corpus = ["北京是中国的首都", "苹果是一种水果", "Python 是一门编程语言", "巴黎位于法国"]
corpus_emb = model.encode(corpus, convert_to_tensor=True)

# 查询
query = "中国的首都在哪里"
query_emb = model.encode(query, convert_to_tensor=True)

# 取 top-2
hits = util.semantic_search(query_emb, corpus_emb, top_k=2)
for hit in hits[0]:
    print(corpus[hit['corpus_id']], hit['score'])
```

## 需要注意的点

- **首次加载会从 HuggingFace 下载模型**,国内环境注意配置镜像(`HF_ENDPOINT=https://hf-mirror.com`)或提前下载到本地
- 向量维度由模型决定,**不同模型生成的向量不能互相比较**
- 长文本会被截断(一般 256 或 512 token),处理长文档要自己切分
- 如果有领域数据(法律、医疗等),用自己的数据**微调**(`fit()` 方法)效果会比通用模型好很多

需要我深入讲哪一块?比如微调流程、和 FAISS 的集成,或者中文模型的具体选型对比?