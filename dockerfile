FROM python:3.8-slim

# 安装必要工具
RUN apt-get update && apt-get install -y wget

# 下载并安装 JDK
# RUN wget https://repo.huaweicloud.com/java/jdk/8u202-b08/jdk-8u202-linux-x64.tar.gz && \
#     mkdir -p /usr/local/java && \
#     tar -xzf jdk-8u202-linux-x64.tar.gz -C /usr/local/java && \
#     rm -rf jdk-8u202-linux-x64.tar.gzF

# 直接设置环境变量 - 这是关键部分
# ENV JAVA_HOME=/usr/local/java/jdk1.8.0_202
# ENV PATH=$PATH:$JAVA_HOME/bin

# 验证 Java 安装
# RUN java -version

WORKDIR /app

# 安装 python 依赖
COPY requirements.txt ./
RUN pip install uv
RUN uv pip install --system  -r requirements.txt && \
    rm -rf /root/.cache/pip /root/.cache/uv /tmp/* /var/tmp/*
# --no-cache-dir

# 移入代码
COPY src .
COPY static ./static
# COPY web ./web
COPY libs ./libs

EXPOSE 8002
# "--app-dir", "src",
# 执行
CMD ["uvicorn",  "app:app", "--port", "8002", "--host", "0.0.0.0"]