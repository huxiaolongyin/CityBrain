import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8012,
        reload=True,
        # 使用完整路径格式排除data目录及其所有子目录
        reload_excludes=[
            "data/*",  # 排除data目录下的所有文件
            "data/*/",  # 排除data的直接子目录
            "data/*/*",  # 排除data子目录下的文件
            "data/*/*/",  # 排除data的孙子目录
            "data/*/*/*",  # 排除data的孙子目录下的文件
            "data/*/*/*/*",  # 更深层级的文件
        ],
    )
