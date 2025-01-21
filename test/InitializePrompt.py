import requests
from logger import logger

# 定义 FastAPI 服务的地址
BASE_URL = "http://127.0.0.1:8000"
USER_ENDPOINT = "/auth"
PROMPT_ENDPOINT = "/prompts"
QUESTION_ENDPOINT = "/questions"


prompt_template = """
请根据以下结构回答问题：
1. 简要回应问题，明确目标和原则。
2. 详细展开行动方案，每个要点不超过 3 行，逻辑清晰，层次分明。
3. 引用相关政策或讲话作为支持性论据，不要显得刻意。
4. 使用朴实流畅的语言，控制答案在 250-300 字范围内，时长约 3 分钟。
问题是：
"""

# 1. 创建管理员用户
def create_admin_user():
    url = f"{BASE_URL}{USER_ENDPOINT}"
    data = {
        "username": "luren2",
        "password": "luren2",
        "user_type": "user",
        "status": "active",
        "model_quota": 10,
    }
    try:
        logger.info(f"Creating admin/user with data: {data}")
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Admin user created: {result}")
        return result  # 返回用户信息
    except requests.exceptions.RequestException as e:
        logger.error(f"Error creating admin user: {e}")
        return None

# 2. 添加一个模版
def add_prompt(user_id: int):
    url = f"{BASE_URL}{PROMPT_ENDPOINT}"
    data = {
        "content": prompt_template,
        "user_id": user_id
    }
    try:
        logger.info(f"Adding prompt with data: {data}")
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Prompt added: {result}")
        return result  # 返回模版信息
    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding prompt: {e}")
        return None

# 3. 写入 `questions_and_answers` 表
def add_question(user_id: int, prompt_id: int, question_content: str):
    url = f"{BASE_URL}{QUESTION_ENDPOINT}"
    data = {
        "question_content": question_content,
        "user_id": user_id,
        "prompt_id": prompt_id
    }
    try:
        logger.info(f"Adding question with data: {data}")
        response = requests.post(url, json=data)
        response.raise_for_status()
        result = response.json()
        logger.info(f"Question added: {result}")
        return result  # 返回问题信息
    except requests.exceptions.RequestException as e:
        logger.error(f"Error adding question: {e}")
        return None


# 主测试流程
if __name__ == "__main__":
    # Step 1: 创建管理员用户
    admin_user = create_admin_user()
    if not admin_user:
        logger.error("Failed to create admin user. Exiting...")
        exit(1)
    
    user_id = admin_user.get("id")

    # # Step 2: 添加一个模版
    # prompt = add_prompt(user_id)
    # if not prompt:
    #     logger.error("Failed to add prompt. Exiting...")
    #     exit(1)
    
    # prompt_id = prompt.get("id")

    # # Step 3: 写入问题
    # question_template = """
    #                     为吸引青年人才来本地就业发展，某市打造多家青年驿站，为外地求职青年提供一周内免费住宿。
    #                     为进一步提高青年驿站服务质量，团市委决定为入住者提供就业指导和城市融入等服务。
    #                     假如由你负责，你怎么做？
    #                     """
    # question = add_question(user_id, prompt_id, question_template)
    # if not question:
    #     logger.error("Failed to add question.")
    #     exit(1)

    logger.info("Test completed successfully.")
