

IMAGE_NAME = citybrain_bigdata
VERSION = latest

.PHONY: dev
dev:
	docker compose -f docker-compose-dev.yml up -d --build

.PHONY: prod
prod:
	docker compose -f docker-compose.yml up -d

# 构建 Docker 镜像
build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

# 保存 Docker 镜像为 tar 文件
.PHONY: save
save: build
	docker save $(IMAGE_NAME):$(VERSION) -o docker_images/$(IMAGE_NAME)-$(VERSION).tar