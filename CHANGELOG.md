# Changelog

这个项目的所有值得注意的变化都将记录在这个文件中。

这个格式基于 [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)，还有这个原则遵循 [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [unreleased]
### Added
- 将任务、事件指标改为真实数据
### Changed
### Fixed
- 修复 mongodb 的大小写导致的数据采集搜索异常
### Removed

## [0.0.2] - 2025-06-24

### Added
- 新增 Collect 接口通过 jinja2 对接 Airflow + DATAX 服务
- 新增 设备状态统计
- 新增 机器人任务统计、异常数据监控分析、机器人事件 指标
- 新增 指标查询的安全审计功能
- 新增 docker容器打包、保存脚本
- 新增 指标导出接口

### Changed
- 集群设备统计改为 * 5

### Fixed
- 修复 collects接口某些字段缺失的问题
- 修复 初始化 SQL 脚本问题，去除city_brain创建，已经在docker-compose.yml中创建
- 修复 requirements.txt 中缺少 psutil、httpx 的问题
- 修复 数据采集功能中数据接入的table命名问题，有的要加前缀 database_name，有的不用


## [0.0.1] - 2025-05-15

初始化版本

### Added
- 新增项目说明 README.md
- 新增变更日志 CHANGELOG.md
- 新增计划 TODO.md
- 新增项目版本 version.txt
- 新增 docker-compose.yml 及 docker-compose-dev.yml 部署
- 新增达梦及 mongo-spark 的jar驱动
- 新增服务日志采集 logger.py
- 新增 fastapi 定义的接口服务，提供模拟数据
- 新增 pgsql 数据库的 ORM
- 新增 database、collect 的 model、schema、service、api
- 将 fastapi 提供的 swagger-ui 的静态文件放到本地进行加载



