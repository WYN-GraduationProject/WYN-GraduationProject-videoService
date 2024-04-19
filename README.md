# 王亚宁毕业设计-视频处理 Web 服务

> 项目为王亚宁本科毕业设计中的视频 Web API 部分

## 项目架构

> 采用 DDD 领域驱动设计架构
> - 应用层（Application Layer）：server.py
> - 领域层（Domain
    Layer）: [python_common/](https://github.com/WYN-GraduationProject/WYN-GraduationProject-common/tree/main/python_common)
> - 基础设施层（Infrastructure Layer）：web/

## 项目技术栈

> - openCV
>- gRPC
>- Nacos
>- fastapi
>- Docker
>- GitHub actions

## 功能

> - 通过 gRPC 实现具体业务处理的 rpc 请求
> - 通过 fastapi 实现视频处理 Web 服务的服务端
>- 通过 openCV 实现视频流的读取和保存
>- 通过 Nacos 实现服务注册与发现
>- 通过 Docker 实现容器化部署
>- 通过 GitHub actions 实现 CI/CD