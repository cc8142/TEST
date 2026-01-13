# 自动化测试工程师作品集（5 年经验）

![自动化架构图](docs/automation-architecture.svg)

[English](README.md)

## 亮点
- 生产级分层：client -> service -> page objects + pytest fixture
- 环境治理：`config/environments.json` + 环境变量覆盖，本地 demo 可离线运行
- 稳定性：重试策略、flaky 复跑、套件标签、并行能力
- 可观测：JUnit XML + HTML 总览 + 可选 Allure
- CI-ready：提供 Jenkinsfile 与 GitLab CI 模板

## 技术栈
- 语言：Python
- 框架：Pytest、Requests、Playwright
- 报告：Allure、JUnit XML、自定义汇总页
- CI/CD：Jenkins、GitLab CI
- 其他：数据工厂、质量度量、稳定性治理

## 快速运行（离线）
- 安装基础依赖：`pip install -r requirements.txt`
- 冒烟门禁：`python tests/run_all.py --suite smoke --env local`
- API 回归：`python tests/run_all.py --suite api --env local`
- UI 契约（无浏览器）：`python tests/run_all.py --suite ui --env local`
- 真浏览器（可选）：`pip install -r requirements-ui.txt` 后执行 `python -m playwright install`
- 运行真浏览器：`python tests/run_all.py --suite ui --env local --headed`
- Playwright 失败 trace：`PW_TRACE=1`
- 并行 + 复跑：`python tests/run_all.py --suite api --workers 2 --reruns 2`
- HTTP 重试仅对幂等方法与短暂状态码生效
- 生成 Allure HTML：`python tests/run_all.py --suite api --allure-report`
- 清理产物：`scripts/clean_reports.ps1` / `scripts/clean_reports.sh`
- Windows 脚本：`scripts/run_demo.ps1`
- Bash 脚本：`scripts/run_demo.sh`

输出：`reports/summary.html`、`reports/summary.json`、`reports/junit.xml`、`reports/artifacts/`（summary 包含 reruns/flaky 与失败分类）。

## Allure 报告（可选）
- 生成：`allure generate reports/allure-results -o reports/allure-report --clean`
- 打开：`allure open reports/allure-report`

## Python 版本
- 已验证：Python 3.10 / 3.11 / 3.12

## 环境变量
- 完整列表见 `.env.example`
- 常用项：`ENV`、`BASE_URL`、`HTTP_TIMEOUT`、`VERIFY_SSL`、`BROWSER`、`HEADLESS`、`PW_TRACE`、`REDACT_KEYS`、`TEST_USERNAME`、`TEST_PASSWORD`、`TEST_TENANT_PREFIX`

## 本地 Demo Server
- `ENV=local` 时自动启动，绑定空闲端口
- 运行时的 base_url 会写入 `reports/summary.json` 与 Allure 元数据

## 失败定位示例
- 先看 `reports/summary.html` 定位失败用例
- 在 Allure 中查看步骤与请求/响应附件
- UI 失败时查看 `reports/artifacts/` 截图

## 工程化护栏
- 安装开发依赖：`pip install -r requirements-dev.txt`
- 启用 pre-commit：`pre-commit install`
- 安全扫描：`bandit -r framework tests`

## 依赖锁定
- 全量锁定（含 UI 依赖）：`pip install -r requirements.lock`

## 套件说明
- `smoke`：PR 门禁，快速回归
- `api`：接口回归
- `ui`：UI 契约 + 可选真浏览器
- `e2e`：端到端流程

## 稳定性控制
- 单用例复跑优先：`@pytest.mark.flaky(reruns=2, reruns_delay=1)`
- 全局复跑仅用于临时场景（`--reruns`）

## 仓库结构
- `framework/`：配置、HTTP 客户端、重试、数据工厂、断言
- `tests/api/services/`：接口服务层
- `tests/ui/pages/`：页面对象
- `config/`：环境配置
- `docs/`：策略、框架、CI、指标、数据/环境
- `scripts/`：运行脚本

## 如何阅读
1. `docs/strategy.md` 了解方法论
2. `docs/framework.md` 了解架构与分层
3. `docs/ci.md` 与 `docs/metrics.md` 了解执行与指标
4. `docs/case-study.md` 了解项目案例

## 备注
- Playwright 为可选依赖，未安装时浏览器用例自动跳过
- 默认使用本地 Demo Server，远程环境可设置 `BASE_URL`
- 默认禁用 pytest 自动插件加载，可通过 `PYTEST_DISABLE_PLUGIN_AUTOLOAD=0` 重新启用
