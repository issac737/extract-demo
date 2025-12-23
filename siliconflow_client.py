"""
SiliconFlow API 客户端 - 兼容 OpenAI 接口
"""
from openai import OpenAI
import os
import sys
import codecs

# Windows控制台UTF-8编码
if sys.platform == "win32":
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

# 加载.env文件
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

load_env()


class SiliconFlowClient:
    """SiliconFlow API 客户端,兼容现有接口"""

    def __init__(self, api_key=None):
        """
        初始化 SiliconFlow 客户端
        Args:
            api_key: API密钥,如果不提供则从环境变量读取
        """
        if api_key is None:
            api_key = os.getenv('SILICONFLOW_API_KEY')

        if not api_key:
            raise ValueError(
                "未设置 SILICONFLOW_API_KEY!\n"
                "请在 .env 文件中设置或传入 api_key 参数"
            )

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )

        print("✓ SiliconFlow API 客户端初始化成功")

    def chat_completion(self, messages, max_tokens=2000, temperature=0.7, top_p=0.9):
        """
        聊天补全接口,兼容 HuggingFace InferenceClient
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            max_tokens: 最大生成token数
            temperature: 温度参数
            top_p: nucleus sampling参数
        Returns:
            包含 choices 的响应对象
        """
        response = self.client.chat.completions.create(
            model="Qwen/Qwen3-8B",
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            stream=False
        )

        # 已经是兼容格式,直接返回
        return response


def test_siliconflow():
    """测试 SiliconFlow API"""
    print("="*80)
    print("测试 SiliconFlow API")
    print("="*80)

    try:
        client = SiliconFlowClient()

        messages = [
            {"role": "user", "content": "你好,请用一句话介绍一下你自己。"}
        ]

        print("\n发送测试消息...")
        response = client.chat_completion(messages, max_tokens=100)

        print("\n模型回复:")
        print(response.choices[0].message.content)
        print("\n" + "="*80)
        print("✓ 测试成功!")
        return True

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        return False


if __name__ == "__main__":
    test_siliconflow()
