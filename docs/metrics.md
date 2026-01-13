# 质量度量与结果展示

## 指标体系
- 覆盖率：接口覆盖率、核心流程覆盖率
- 通过率：回归稳定性、构建成功率
- 缺陷密度：按模块统计缺陷密度与趋势
- 回归效率：回归耗时与人力节省

## 指标口径
- 统计周期：按周与按版本
- 统计方法：自动统计 + 人工校验
- 异常处理：排除环境波动用例，保留波动标签

## 产出物
- `reports/summary.json`：total/passed/failed/skipped/duration/by_suite/slow_tests
- `reports/summary.html`：面向评审的可读汇总页
- `reports/junit.xml`：CI 统一接入标准
- `reports/artifacts/`：失败截图与附件
- `reports/allure-results/`：可选 Allure 报告
- `reports/allure-report/`：Allure HTML 报告

## 结果展示与改进
- 结果趋势：覆盖率从 20% 提升到 78%
- 稳定性：flaky 率从 15% 降到 2%
- 效率：版本回归从 2 天缩短到 3 小时
