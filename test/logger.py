import logging

# 创建日志器
logger = logging.getLogger("my_logger")
logger.setLevel(logging.INFO)

# 创建终端输出的处理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 创建文件输出的处理器
file_handler = logging.FileHandler("app.log")
file_handler.setLevel(logging.INFO)

# 设置日志格式
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# 添加处理器到日志器
logger.addHandler(console_handler)
logger.addHandler(file_handler)