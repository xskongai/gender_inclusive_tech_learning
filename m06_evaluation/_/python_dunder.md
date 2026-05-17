Python 的 dunder 方法（也叫 **magic methods**）非常多，下面按使用场景分类列出最常用的那些。

## 1. 对象创建与初始化

```python
class MyClass:
    def __new__(cls, *args, **kwargs):   # 创建实例（很少重写）
        return super().__new__(cls)
    
    def __init__(self, x):               # 初始化实例（最常用）
        self.x = x
    
    def __del__(self):                   # 析构（对象被销毁时调用，慎用）
        pass
```

## 2. 字符串表示

```python
class Point:
    def __init__(self, x, y):
        self.x, self.y = x, y
    
    def __repr__(self):                  # 给开发者看，调试用
        return f"Point({self.x}, {self.y})"
    
    def __str__(self):                   # 给用户看，print() 时调用
        return f"({self.x}, {self.y})"
    
    def __format__(self, spec):          # f-string / format() 调用
        return f"{self.x}:{self.y}"
```

经验：**至少实现 `__repr__`**，因为 `__str__` 没定义时会回退到 `__repr__`。

## 3. 比较运算

```python
class Item:
    def __eq__(self, other): ...         # ==
    def __ne__(self, other): ...         # !=（一般不用写，自动反转 __eq__）
    def __lt__(self, other): ...         # 
    def __le__(self, other): ...         # <=
    def __gt__(self, other): ...         # >
    def __ge__(self, other): ...         # >=
    def __hash__(self): ...              # 让对象可以放进 set / dict 的 key
```

提示：定义了 `__eq__` 后，`__hash__` 会被自动设为 `None`，对象就不可哈希了。如果需要哈希，要显式定义 `__hash__`。

## 4. 算术运算

```python
class Vec:
    def __add__(self, other): ...        # +
    def __sub__(self, other): ...        # -
    def __mul__(self, other): ...        # *
    def __truediv__(self, other): ...    # /
    def __floordiv__(self, other): ...   # //
    def __mod__(self, other): ...        # %
    def __pow__(self, other): ...        # **
    def __neg__(self): ...               # -x（一元负号）
    def __abs__(self): ...               # abs(x)
```

还有 `__radd__`、`__rsub__` 等"反向"版本，处理 `3 + obj` 这种情况（左操作数不支持时调用右操作数的反向方法）。

## 5. 容器协议

```python
class MyList:
    def __len__(self):                   # len(obj)
        return len(self.data)
    
    def __getitem__(self, key):          # obj[key]
        return self.data[key]
    
    def __setitem__(self, key, value):   # obj[key] = value
        self.data[key] = value
    
    def __delitem__(self, key):          # del obj[key]
        del self.data[key]
    
    def __contains__(self, item):        # item in obj
        return item in self.data
    
    def __iter__(self):                  # for x in obj
        return iter(self.data)
    
    def __next__(self):                  # 配合 __iter__ 实现迭代器
        ...
    
    def __reversed__(self):              # reversed(obj)
        ...
```

## 6. 可调用对象

```python
class Adder:
    def __init__(self, n):
        self.n = n
    
    def __call__(self, x):               # 让实例像函数一样被调用
        return x + self.n

add5 = Adder(5)
add5(10)  # 15
```

## 7. 上下文管理器（`with` 语句）

```python
class Resource:
    def __enter__(self):                 # 进入 with 块
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):  # 离开 with 块
        # 清理资源
        return False  # 不抑制异常

with Resource() as r:
    ...
```

## 8. 属性访问

```python
class Proxy:
    def __getattr__(self, name):         # 访问不存在的属性时调用
        return f"no attribute {name}"
    
    def __setattr__(self, name, value):  # 所有属性赋值都会触发（小心递归）
        super().__setattr__(name, value)
    
    def __delattr__(self, name):         # del obj.x
        ...
    
    def __getattribute__(self, name):    # 所有属性访问都触发（慎用，易死循环）
        return super().__getattribute__(name)
```

## 9. 类型转换

```python
class Money:
    def __int__(self): ...               # int(obj)
    def __float__(self): ...             # float(obj)
    def __bool__(self): ...              # bool(obj) / if obj
    def __bytes__(self): ...             # bytes(obj)
    def __index__(self): ...             # 用作切片/索引时的整数
```

提示：没定义 `__bool__` 时会回退到 `__len__`（长度为 0 视为 False）。

## 实战中真正高频的

如果只挑最常实现的，大概是这几个：

```python
__init__       # 几乎每个类都要
__repr__       # 调试必备
__str__        # 用户友好的字符串
__eq__         # 比较相等
__hash__       # 配合 __eq__，用于 set/dict
__len__        # 容器类
__iter__       # 可迭代
__getitem__    # 索引访问
__enter__/__exit__  # 资源管理
__call__       # 函数对象 / 装饰器类
```

其他的等你真的需要时再查就行。日常写业务代码 80% 的情况只会用到 `__init__` 和 `__repr__`。