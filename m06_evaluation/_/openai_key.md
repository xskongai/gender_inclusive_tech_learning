# 在 PyCharm 中更新 `.env` 里的 API Key

## 最简单的方式：直接编辑 `.env` 文件

1. 在 PyCharm 左侧 **Project 面板**找到项目根目录下的 `.env` 文件
   - 路径：`gender_inclusive_tech_learning/.env`
   - 如果看不到，点项目面板右上角的齿轮 ⚙️ → 取消勾选 "Hide ignored files"（`.env` 通常被 `.gitignore` 排除，PyCharm 有时会灰显但还是能打开）

2. 双击打开，找到这一行：
   ```
   OPENAI_API_KEY=sk-proj-lW...C70A
   ```

3. 替换成新 key：
   ```
   OPENAI_API_KEY=sk-proj-新的key内容
   ```

4. **Cmd+S** 保存

## ⚠️ 几个容易踩的坑

**不要加引号**（python-dotenv 在某些版本会把引号当成 key 的一部分）：
```
✅ OPENAI_API_KEY=sk-proj-abc123
❌ OPENAI_API_KEY="sk-proj-abc123"
❌ OPENAI_API_KEY='sk-proj-abc123'
```

**等号两边不要空格**：
```
✅ OPENAI_API_KEY=sk-proj-abc123
❌ OPENAI_API_KEY = sk-proj-abc123
```

**末尾不要有空格或换行符**：复制 key 的时候很容易尾巴上带个空格。粘贴后把光标移到行尾按 `End` 检查一下。

**从 OpenAI 后台复制 key 时**：用「Copy」按钮复制，不要手动框选，避免漏字符或带不可见字符。

## 验证是否生效

保存后重新运行 `llm_judge.py`，看日志这一行：
```
[config] OPENAI_API_KEY: len=164, prefix=sk-proj-lW, suffix=C70A
```

- `prefix` 和 `suffix` 应该变成新 key 的前后缀
- 如果还是显示老的 `C70A` → PyCharm 可能缓存了旧环境变量，看下一节

## 如果还是读到老 key

PyCharm 的 **Run Configuration** 里可能硬编码了环境变量，会覆盖 `.env`：

1. 点右上角运行配置下拉 → **Edit Configurations...**
2. 找到 `llm_judge` 这个配置
3. 看 **Environment variables** 那一栏
4. 如果里面有 `OPENAI_API_KEY=sk-proj-...C70A`，把它删掉或更新成新 key
5. **Apply** → **OK**

另外，如果你装了 EnvFile 插件，也要去 Run Configuration 里确认它指向的是项目根的 `.env`。

## 顺手做个安全清理

既然这个 key 已经在终端日志里露了前后缀，建议去 OpenAI 后台 **Revoke 掉这个旧 key**（即使它已经失效，撤销操作能让它彻底从你账号下消失，避免混淆）：

https://platform.openai.com/api-keys → 找到 `...C70A` → Delete