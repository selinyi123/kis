# KIS 架构 ARCHITECTURE

## 架构等式
`KIS = ClipVault 采集底座 + DPMS 管道/评分内核 + PPE 证据纪律 + MemOS 记忆运行时`

## 分层
```
来源层    GitHub Stars · 剪切板 · 网页 · X · 知乎 · B站 · 小红书 · 本地 · RSS
   │  插件化连接器（BaseConnector 契约，DPMS providers 范式）
采集层    调度(should_scan) → 抓取 → 原始事件入库
   │
加工管道  清洗 → 注入审计(PPE) → 规范化 → 去重(content_hash)
          → 摘要/分类/打标(LLM候选, v0.2) → 价值评分 → 聚类 → 项目关联 → 生命周期
   │  统一 KnowledgeCard（版本化 schema）
存储层    v0.1 SQLite+FTS5 →(平滑迁移)→ MemOS 图记忆 ；事实源=事件日志
   │
出口层    Obsidian+GitHub同步 · FTS/向量检索 · codegraph 服务Codex · Web控制台
   │  (v2) 研究报告 · 任务生成 · 知识图谱 · 多模态解析
```

## v0.1 模块（已实现）
| 模块 | 职责 | 复用来源 |
|---|---|---|
| `card.py` | 卡片构建、`stable_id`/`content_hash`、`infer_projects` | DPMS discovery 身份/去重；DPMS strategy 关联 |
| `validate.py` | 零依赖 schema 校验，拒绝未知字段 | PPE 契约层 |
| `store.py` | SQLite+FTS5、幂等 upsert、事件日志 | ClipVault outbox + DPMS insert_if_new |
| `obsidian.py` | frontmatter + wikilink 渲染导出 | ClipVault Obsidian |
| `scripts/ingest_github_stars.py` | Stars 连接器（gh CLI 复用） | ClipVault gh 用法 |

## 关键设计决策（v0.1 冻结）
1. **底座**：新建独立 `kis` repo（用户拍板），复用三仓的*模式*而非代码耦合。
2. **身份/幂等**：`id = kc_<16hex(sha256(connector|url))>` 主键；`content_hash` 决定 inserted/updated/unchanged。
3. **确定性 vs LLM 分离**：v0.1 全确定性；enrichment 字段已在 schema 中预留默认值，v0.2 接 LLM 不破坏契约。
4. **存储渐进**：先 SQLite+FTS5（已验证），v0.3 迁 MemOS，schema 保持兼容。
5. **零第三方依赖**：手写最小 JSON-Schema 校验器，FTS5 不可用时降级 LIKE。
6. **安全门禁（v0.2）**：删除/外发/覆盖套 DPMS `tighten_action`（只能更保守）。

## 连接器契约（v0.2 落地）
```python
class BaseConnector:
    name: str
    def discover(self) -> Iterable[RawItem]: ...   # 列出候选
    def fetch(self, item) -> RawContent: ...        # 取正文
    def normalize(self, raw) -> KnowledgeCard: ...  # 转统一卡片
```
GitHub Stars 连接器是该契约的参考实现（当前以脚本形态，v0.2 抽象为类）。
