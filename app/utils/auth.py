import os
import app.config.settings as settings

def verify_password(input_password):
    """
    验证用户输入的密码是否正确
    
    Args:
        input_password (str): 用户输入的密码
        
    Returns:
        bool: 密码是否正确
    """
    return input_password == settings.PASSWORD 