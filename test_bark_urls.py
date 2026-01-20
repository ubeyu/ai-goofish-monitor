import os
import sys
from src.infrastructure.config.settings import NotificationSettings

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 测试 NotificationSettings.get_bark_urls() 方法
def test_get_bark_urls():
    print("测试 NotificationSettings.get_bark_urls() 方法...")
    
    # 测试场景1: 只配置了 BARK_URL
    os.environ["BARK_URL"] = "https://api.day.app/KEY1/"
    os.environ.pop("BARK_URLS", None)
    
    settings = NotificationSettings()
    urls = settings.get_bark_urls()
    print(f"场景1 - 只配置 BARK_URL: {urls}")
    assert len(urls) == 1
    assert urls[0] == "https://api.day.app/KEY1/"
    
    # 测试场景2: 只配置了 BARK_URLS
    os.environ.pop("BARK_URL", None)
    os.environ["BARK_URLS"] = "https://api.day.app/KEY2/,https://api.day.app/KEY3/"
    
    settings = NotificationSettings()
    urls = settings.get_bark_urls()
    print(f"场景2 - 只配置 BARK_URLS: {urls}")
    assert len(urls) == 2
    assert urls[0] == "https://api.day.app/KEY2/"
    assert urls[1] == "https://api.day.app/KEY3/"
    
    # 测试场景3: 同时配置了 BARK_URL 和 BARK_URLS
    os.environ["BARK_URL"] = "https://api.day.app/KEY1/"
    os.environ["BARK_URLS"] = "https://api.day.app/KEY2/,https://api.day.app/KEY3/"
    
    settings = NotificationSettings()
    urls = settings.get_bark_urls()
    print(f"场景3 - 同时配置 BARK_URL 和 BARK_URLS: {urls}")
    assert len(urls) == 3
    assert urls[0] == "https://api.day.app/KEY1/"
    assert urls[1] == "https://api.day.app/KEY2/"
    assert urls[2] == "https://api.day.app/KEY3/"
    
    # 测试场景4: 空配置
    os.environ.pop("BARK_URL", None)
    os.environ.pop("BARK_URLS", None)
    
    settings = NotificationSettings()
    urls = settings.get_bark_urls()
    print(f"场景4 - 空配置: {urls}")
    assert len(urls) == 0
    
    # 测试场景5: BARK_URLS 包含空字符串
    os.environ["BARK_URLS"] = "https://api.day.app/KEY1/, ,https://api.day.app/KEY2/"
    
    settings = NotificationSettings()
    urls = settings.get_bark_urls()
    print(f"场景5 - BARK_URLS 包含空字符串: {urls}")
    assert len(urls) == 2
    assert urls[0] == "https://api.day.app/KEY1/"
    assert urls[1] == "https://api.day.app/KEY2/"
    
    print("所有测试通过!")

if __name__ == "__main__":
    test_get_bark_urls()
