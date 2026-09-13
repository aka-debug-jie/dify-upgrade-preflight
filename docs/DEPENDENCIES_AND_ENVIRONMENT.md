# 依赖、环境和工具选择

## 1. 原则

用标准库做 CLI、JSON、日志、哈希、受限子进程。候选运行依赖仅 Pydantic / PyYAML / packaging；P00 核验版本、许可证、wheel 与支持 Python 后固定。未批准前不自动添加其它核心依赖。

开发候选 pytest、pytest-cov、Hypothesis、Ruff、mypy、build。性能尽量用标准库计时和平台资源计量，不引入常驻采样代理。

分发包名候选 `dify-upgrade-preflight`；导入模块 `dify_preflight`；CLI `dify-preflight`。P00 查重但不注册名称、不创建远程项目。

## 2. Python 与安装

首版计划在 Python 3.11/3.12/3.13 上测试。优先在现有 Linux 环境创建项目虚拟环境；macOS 做离线核心验证。不可修改全局 Python、安装系统级 Docker、sudo 或修改驱动。

允许选择 uv 维护开发锁文件；产品用户不必安装 uv。应用依赖边界与开发锁不同：锁文件固定开发/CI 环境，发布元数据用经过矩阵验证的范围，不无限 pin 所有用户依赖。

P01 在 pyproject 定义 `.[dev]`，实际创建后再运行：

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
python -m pytest tests/unit tests/contract -q
python -m ruff check .
python -m mypy src/dify_preflight
```

激活项目虚拟环境是开发动作，和禁止 source **生产 .env 数据文件**不同。缺少网络/包时记录，不偷偷改用不同依赖组合。

## 3. Docker Compose

核心 check 无 Docker 依赖。snapshot 依赖一个经 P00/P02 fixture 验证的 Compose 版本；不要凭 Dify release 大小猜最低 Compose 版本。

P00 记录已有 `docker compose version`，只读能力检查，不连接生产 daemon。正式原生解析 tests 可以在已明确允许的独立环境运行；只有 P08 才涉及经批准的服务启动。

## 4. CI

阶段先实现本地可运行命令，再写 CI。PR 使用无秘密权限；第三方 Actions 固定 commit，依赖下载与产品离线测试明确分开。

契约验证、格式/类型、unit/contract、隐私、轮子安装、catalog 校验为门禁。Compose 集成和性能是独立 job；不能因为 runner 没 Docker 就把全部测试标为通过。

不使用 pull_request_target 去执行未经信任的 PR 代码。发布 workflow 初始只生成待发布产物，不带自动上传授权。

## 5. 性能不靠 GPU

项目不使用 CUDA、不需要模型推理。主要优化方向是少启动外部进程、一次规范化、索引化字段、输入大小上限和延迟导入；不要为了用现有显卡而增加功能。
