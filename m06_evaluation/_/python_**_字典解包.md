# Python 中 `**` 的解包语法

在 `{**p, **scores}` 这个写法里，`**` 是**字典解包**（dictionary unpacking）操作符，用来把一个字典"摊开"合并到另一个字典里。

## 核心作用

```python
p = {"name": "Alice", "age": 30}
scores = {"math": 90, "english": 85}

result = {**p, **scores}
# 结果: {"name": "Alice", "age": 30, "math": 90, "english": 85}
```

相当于把 `p` 和 `scores` 的所有键值对**合并成一个新字典**。

## 几个重点

**1. 合并字典，不修改原字典**

`**` 解包会生成一个新字典，`p` 和 `scores` 本身不变。

**2. 键冲突时，后面的覆盖前面的**

```python
a = {"x": 1, "y": 2}
b = {"y": 99, "z": 3}
{**a, **b}  # {"x": 1, "y": 99, "z": 3}  ← y 被 b 覆盖
```

所以 `{**p, **scores}` 里如果 `p` 和 `scores` 有同名 key，`scores` 的值会胜出。

**3. 可以混合普通键值对**

```python
{**p, "extra": 100, **scores}  # 都可以放在一起
```

**4. `*` 和 `**` 的区别**

- `*` 用来解包**可迭代对象**（list、tuple 等）→ 一般用在列表或函数参数里
- `**` 用来解包**字典** → 一般用在字典或关键字参数里

```python
# 列表解包
nums = [1, 2, 3]
[*nums, 4, 5]  # [1, 2, 3, 4, 5]

# 字典解包
{**p, **scores}
```

## 回到你那行代码

```python
results.append({**p, **scores})
```

意思是：把 `p` 和 `scores` 合并成一个新字典，然后追加到 `results` 列表里。常见于处理一组记录时，把"基础字段"和"计算出来的字段"拼在一起再存起来。

等价的写法（Python 3.9+）也可以用 `|`：

```python
results.append(p | scores)
```

效果一样，但 `{**p, **scores}` 兼容性更好，老代码里很常见。