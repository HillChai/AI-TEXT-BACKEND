import requests
from logger import logger

# 定义测试参数
url = "http://127.0.0.1:8000/gpt"  # FastAPI 服务的地址

prompt_template = """
请根据以下结构回答问题：
1. 简要回应问题，明确目标和原则。
2. 详细展开行动方案，每个要点不超过 3 行，逻辑清晰，层次分明。
3. 引用相关政策或讲话作为支持性论据，不要显得刻意。
4. 使用朴实流畅的语言，控制答案在 250-300 字范围内，时长约 3 分钟。
问题是：
"""

# 构造请求数据
data = {
    "user_id": 3,
    "question_content": "75岁的詹大爷一个人居住在车库里，以捡废品为生。但是，詹大爷经常把捡来的废品放在消防通道里，阻碍小区居民的日常通行，也会有噪声和异味发出。一日，詹大爷又把废品放在消防通道里，并因此与其他居民起了争执。如果你是社区工作人员，你会怎么做？请现场模拟。",
    "prompt_id": 1
}

# 发起 POST 请求
try:
    response = requests.post(url, json=data)
    response.raise_for_status()  # 检查 HTTP 状态码是否为 200
    result = response.json()  # 获取返回的 JSON 数据

    # 打印结果
    logger.info(f"API Response: {result}")
except requests.exceptions.RequestException as e:
    logger.error(f"Error while calling the API: {e}")
except ValueError as e:
    logger.error(f"Error while parsing API response: {e}")