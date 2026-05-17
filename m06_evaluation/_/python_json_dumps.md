# `json.dumps()` 是什么意思

`json.dumps()` 是 Python 标准库 `json` 模块里的一个函数,作用是把 Python 对象(比如字典、列表)**转换成 JSON 格式的字符串**。

"dumps" 的意思是 "dump string"(导出为字符串)。对比一下:
- `json.dump()` — 把对象写入文件
- `json.dumps()` — 把对象转成字符串(多了个 s 代表 string)
- `json.loads()` — 反过来,把 JSON 字符串解析成 Python 对象

## 你这段代码在做什么

```python
return json.dumps({
    "gender_assumption": g_assumption,
    "gender_neutrality": g_neutrality,
    "quality_relevance": q_relevance,
    "reasoning": f"Rule-based: {bias_count} biased words in original, "
                 f"neutrality_rate={scores['neutrality_rate']:.2f}, "
                 f"overlap={scores['content_overlap']:.2f}",
})
```

这里先构造了一个 Python 字典(`{...}`),然后用 `json.dumps()` 把它转成 JSON 字符串再返回。

**转换前**(Python 字典对象):
```python
{"gender_assumption": 0.8, "gender_neutrality": 0.5, ...}
```

**转换后**(JSON 字符串,可以打印、传输、存到数据库):
```
'{"gender_assumption": 0.8, "gender_neutrality": 0.5, ...}'
```

## 为什么要这么做

通常有这几种场景:
- 函数需要返回字符串(比如给前端 API、写日志、存数据库),不能直接返回 Python 字典
- 跨语言/跨进程通信,JSON 是通用格式
- 调用方期望拿到字符串再自己解析

## 常用参数

```python
json.dumps(data, indent=2, ensure_ascii=False)
```

- `indent=2` — 美化输出,加缩进,方便阅读
- `ensure_ascii=False` — 保留中文等非 ASCII 字符,否则会被转成 `\uXXXX` 这种转义形式(对中文很重要)

举个例子:
```python
json.dumps({"name": "张三"})              # '{"name": "\u5f20\u4e09"}'
json.dumps({"name": "张三"}, ensure_ascii=False)  # '{"name": "张三"}'
```