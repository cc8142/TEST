# 测试数据与环境治理

## 配置文件
- `config/environments.json`：统一维护 base_url/timeout/ssl 等环境画像
- ENV 变量：`ENV=local|test|staging` 选择环境
- `.env.example`：环境变量清单模板

## 环境变量覆盖
- `BASE_URL`：临时指定环境地址
- `HTTP_TIMEOUT`：HTTP 超时（秒）
- `VERIFY_SSL`：是否校验证书（true/false）
- `BROWSER`：浏览器类型（chromium/firefox/webkit）
- `HEADLESS`：是否无头模式（1/0）
- `PW_TRACE`：是否保留 Playwright 失败 trace（1/0）
- `ARTIFACT_DIR`：失败产物输出目录
- `TEST_USERNAME`：测试账号用户名（默认 demo）
- `TEST_PASSWORD`：测试账号密码（默认 pass）
- `TEST_TENANT_PREFIX`：租户/数据前缀（用于隔离）

## 数据准备
- 数据来源：优先通过 API 构造，必要时使用 SQL 兜底
- 数据隔离：按租户/账号隔离，避免并行污染
- 数据回收：用例结束自动清理，核心数据保留用于复现

## 环境管理
- 环境划分：dev/test/staging 多环境并存
- 配置管理：环境变量 + 配置文件切换
- 依赖服务：关键依赖可 Mock，外部依赖可降级

## Mock 与虚拟化
- Mock 方案：服务虚拟化 + 本地桩
- 使用场景：不可控依赖、异常注入、性能边界验证
