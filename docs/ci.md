# CI/CD 集成

## 触发策略
- PR 触发：核心接口冒烟与核心 UI 场景
- 定时触发：夜间全量回归
- 手动触发：发布前回归与紧急验证

## 流水线落地
- `Jenkinsfile`：安装依赖 -> smoke 门禁 -> 可选 UI 套件 -> JUnit/Allure 归档
- `.gitlab-ci.yml`：smoke/regression stages，带缓存、JUnit 报告、artifacts 过期策略
- 质量门禁：ruff/mypy/bandit 作为独立阶段

## 运行入口
- 统一入口：`python tests/run_all.py --suite smoke --env local`（PR 门禁）
- API 回归：`python tests/run_all.py --suite api --env local`
- 可选参数：`--workers`、`--reruns`、`--headed`、`--browser`

## 并行与资源管理
- 并行方式：按业务域拆分并行执行
- 资源限制：控制并行度，避免环境过载

## 稳定性与失败处理
- 失败重试：只对网络与环境波动类用例重试
- 失败归因：环境/数据/代码三类标签化

## 通知与可视化
- 通知渠道：企业 IM + 邮件
- 报告展示：每日趋势与版本对比

## GitLab CI 落地要点
- Python 版本固定（示例：3.11）
- 依赖安装使用 requirements.lock 作为约束，减少版本漂移
- pip cache + playwright cache（UI job）
- JUnit 报告挂载到 MR
- artifacts 设置 `expire_in`，避免产物膨胀

## Jenkins 落地要点
- 固定 Python 版本或虚拟环境路径
- JUnit 与 Allure 产物发布
- API/UI 并行化
