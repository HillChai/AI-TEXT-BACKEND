import requests
from logger import logger

# 定义 FastAPI 服务的地址
BASE_URL = "http://127.0.0.1:8000"
USER_ENDPOINT = "/users"

def update_user(user_id: int, updated_data: dict):
    """
    更新指定用户信息。
    
    Args:
        user_id (int): 用户 ID。
        updated_data (dict): 要更新的字段及其新值。

    Returns:
        dict: 更新后的用户信息。
    """
    url = f"{BASE_URL}{USER_ENDPOINT}/{user_id}"
    try:
        logger.info(f"Updating user with ID {user_id} and data: {updated_data}")
        response = requests.put(url, json=updated_data)
        response.raise_for_status()
        result = response.json()
        logger.info(f"User updated successfully: {result}")
        return result  # 返回更新后的用户信息
    except requests.exceptions.RequestException as e:
        logger.error(f"Error updating user: {e}")
        return None

# 测试代码
if __name__ == "__main__":
    # 假设我们有一个已存在的用户 ID
    test_user_id = 1  # 替换为实际用户 ID

    # 要更新的用户信息
    updated_data = {
        "username": "CuiPi",
        "status": "active",
        "user_type": "admin",
        "model_quota": 10
    }

    # 调用更新用户信息的函数
    updated_user = update_user(test_user_id, updated_data)

    if updated_user:
        logger.info(f"Updated user info: {updated_user}")
    else:
        logger.error("Failed to update user.")
