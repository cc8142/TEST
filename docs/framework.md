# 自动化框架设计

## 设计目标
- 可维护性：用例只关注业务意图，减少脚本改动范围
- 可扩展性：支持新业务线、新端（Web/移动 Web）
- 稳定性：系统性治理 flaky case
- 可观测性：日志、截图、请求响应可追溯

## 目录结构（落地版）
- `framework/`：配置、HTTP 客户端、重试策略、数据工厂、断言
- `tests/api/services/`：业务接口封装
- `tests/ui/pages/`：页面对象封装
- `tests/conftest.py`：fixture、环境引导、本地服务启动
- `config/environments.json`：环境画像
- `reports/`：summary、junit、artifacts
- `requirements.txt`：基础依赖（含 Playwright）

## 分层结构
- 驱动层：HttpClient / Playwright driver
- 业务层：API services + UI pages
- 用例层：pytest 用例 + markers
- 公共层：retry、logger、data factory

## 稳定性与可观测
- RetryPolicy + reruns，拒绝硬编码 sleep
- 失败自动截屏（Playwright）
- 报告链路：JUnit XML + summary.html + Allure（可选）
