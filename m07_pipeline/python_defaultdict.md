# Python `defaultdict` 重点

`defaultdict` 是 `collections` 模块里的一个字典子类,核心作用是:**访问不存在的 key 时,自动创建一个默认值,而不是抛 `KeyError`**。

## 基本用法

```python
from collections import defaultdict

d = defaultdict(list)
d['a'].append(1)   # 'a' 不存在,自动创建一个空 list
d['a'].append(2)
print(d)  # defaultdict(<class 'list'>, {'a': [1, 2]})
```

构造时传入的参数叫 **`default_factory`**,它必须是一个**可调用对象**(callable),访问缺失 key 时会调用它生成默认值。

## 常见的 default_factory

- `list` → 默认 `[]`,适合分组、追加场景
- `set` → 默认 `set()`,适合去重分组
- `int` → 默认 `0`,适合计数(虽然 `Counter` 更专用)
- `dict` → 默认 `{}`,适合嵌套结构
- `lambda: '默认值'` → 自定义任意默认值

```python
# 计数
counter = defaultdict(int)
for ch in 'mississippi':
    counter[ch] += 1

# 分组
groups = defaultdict(list)
for name, dept in [('Alice','HR'), ('Bob','IT'), ('Cathy','HR')]:
    groups[dept].append(name)

# 自定义默认值
status = defaultdict(lambda: 'unknown')
```

## 几个容易踩的坑

**1. 只是「访问」就会创建 key**

```python
d = defaultdict(list)
_ = d['x']         # 仅仅访问
print('x' in d)    # True!key 已经被创建了
```

如果只想检查存在性,用 `key in d` 或 `d.get(key)`,不要用 `d[key]`。

**2. `default_factory` 必须是 callable,不是值本身**

```python
defaultdict(0)       # ❌ 报错:int 0 不可调用
defaultdict(int)     # ✅ 正确:int 是类,调用 int() 返回 0
defaultdict(lambda: 0)  # ✅ 也行
```

**3. 不传 `default_factory` 时,行为退回普通 dict**

```python
d = defaultdict()    # 没传 factory
d['missing']         # 照样 KeyError
```

**4. 嵌套 defaultdict 用 lambda**

```python
nested = defaultdict(lambda: defaultdict(int))
nested['a']['b'] += 1   # 不会报错
```

## 和普通 dict 的对比

普通 dict 的等价写法通常是 `setdefault` 或 `dict.get`:

```python
# 普通 dict
d = {}
d.setdefault('a', []).append(1)

# defaultdict
d = defaultdict(list)
d['a'].append(1)
```

`defaultdict` 的代码更干净,性能也略好一点(`setdefault` 每次都会构造默认值,即使 key 存在;`defaultdict` 只在缺失时调用 factory)。

## 一个小技巧:用完后「冻结」

如果想把 `defaultdict` 转回普通 dict(比如返回给调用方,避免对方意外创建 key):

```python
result = dict(my_defaultdict)
```

或者临时关闭自动创建行为:

```python
d.default_factory = None
d['missing']   # 现在会抛 KeyError
```

需要我展开讲某个用法或者搭配实际场景(比如图、树、word count)吗?