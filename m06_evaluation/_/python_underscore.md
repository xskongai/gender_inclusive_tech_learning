在 Python 中，以下划线开头的命名是一种**约定**，用来表达不同的访问意图。具体含义如下：

## 单下划线 `_name`

表示"**内部使用**"的弱约定，是给程序员看的提示，并不会被解释器强制限制。

```python
class MyClass:
    def __init__(self):
        self.name = "public"
        self._internal = "internal"  # 暗示：这是内部属性，外部最好别动
    
    def _helper(self):              # 暗示：这是辅助方法
        return "internal use"
```

特点：
- 仍然可以从外部访问（`obj._internal` 是合法的）
- `from module import *` 时，以 `_` 开头的名字**不会**被导入
- 只是一种"君子协定"，告诉使用者"这是实现细节，不属于公开 API"

## 双下划线 `__name`（前缀）

会触发 Python 的 **name mangling（名称改写）** 机制，由解释器强制处理。

```python
class MyClass:
    def __init__(self):
        self.__private = "private"
    
    def __method(self):
        return "mangled"

obj = MyClass()
# obj.__private        # AttributeError!
obj._MyClass__private  # 可以这样访问，但不应该这么做
```

特点：
- 解释器会把 `__private` 自动改写成 `_MyClass__private`
- 主要目的是**避免子类意外覆盖父类属性**，而不是真正的"私有"
- 仍然可以通过改写后的名字访问，所以也不是真正的访问保护

## 顺便提一下：`__name__`（前后双下划线）

这叫 **dunder**（double underscore），是 Python 保留的**特殊方法/属性**，比如 `__init__`、`__str__`、`__len__`。你不应该自己发明这种命名，只应该实现 Python 已经定义好的那些。

```python
class MyClass:
    def __init__(self):       # 构造方法
        pass
    def __str__(self):        # 定义 str(obj) 的行为
        return "my class"
    def __len__(self):        # 定义 len(obj) 的行为
        return 0
```

## 小结

| 命名 | 含义 | 强制性 |
|------|------|--------|
| `_name` | 内部使用，约定俗成 | 无（仅约定） |
| `__name` | 触发名称改写，避免子类冲突 | 有（解释器处理） |
| `__name__` | Python 内置的特殊方法/属性 | 有（语言规定） |

实际项目里，**单下划线用得最多**，双下划线前缀其实用得很少——大多数情况下用单下划线就足够清晰了。