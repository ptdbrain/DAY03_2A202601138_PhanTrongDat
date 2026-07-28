"""
🔌 MULTI-PROVIDER LLM ADAPTER (OpenAI, Gemini, Anthropic, OpenRouter & Offline Mock)
Hỗ trợ chuyển đổi linh hoạt giữa các nhà cung cấp AI chỉ bằng cách đổi biến môi trường LLM_PROVIDER.
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho tất cả các LLM Provider"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env!"
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(
                model=self.model_name,
                contents=contents
            )
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (GPT-4o, GPT-3.5-turbo, etc.)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env!"
        try:
            import openai
            client = openai.OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model_name,
                messages=messages
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude Provider (Claude 3.5 Sonnet, Claude 3 Haiku)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "claude-3-haiku-20240307"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_anthropic_api_key_here":
            return "[Anthropic Error]: Chưa cấu hình ANTHROPIC_API_KEY trong file .env!"
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=self.api_key)
            kwargs = {
                "model": self.model_name,
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }
            if system_prompt:
                kwargs["system"] = system_prompt
                
            response = client.messages.create(**kwargs)
            return response.content[0].text
        except Exception as e:
            return f"[Anthropic Exception]: {str(e)}"


class OpenRouterProvider(BaseLLMProvider):
    """OpenRouter Provider (Hỗ trợ gọi mọi model qua OpenRouter API)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "google/gemini-2.5-flash"
        
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openrouter_api_key_here":
            return "[OpenRouter Error]: Chưa cấu hình OPENROUTER_API_KEY trong file .env!"
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            payload = {
                "model": self.model_name,
                "messages": messages
            }
            res = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload, timeout=30)
            if res.status_code == 200:
                data = res.json()
                return data["choices"][0]["message"]["content"]
            else:
                return f"[OpenRouter API Error {res.status_code}]: {res.text}"
        except Exception as e:
            return f"[OpenRouter Exception]: {str(e)}"


class MockProvider(BaseLLMProvider):
    """Offline Mock Provider (Cho bài test không cần kết nối API)"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        text = prompt.lower()

        if "chatbot baseline" in system_prompt.lower() or "không có khả năng truy cập" in system_prompt.lower():
            if any(word in text for word in ("khóa học", "review", "đánh giá", "data analysis", "machine learning")):
                return (
                    "Final Answer: Tôi là chatbot tư vấn chung, không có khả năng truy cập Internet thời gian thực "
                    "để tra cứu danh sách khóa học hay review mới nhất. Bạn có thể sử dụng phiên bản ReAct Agent."
                )

        if any(word in text for word in ("bom", "vũ khí", "vu khi", "chất nổ", "thuốc nổ")):
            return (
                "Thought: Yêu cầu liên quan đến nội dung nguy hiểm.\n"
                "Final Answer: TỪ CHỐI: Tôi không thể hỗ trợ nội dung chế tạo vũ khí hoặc chất nổ."
            )

        if "observation:" in text and "4.7/5" in text:
            return (
                "Thought: Đã có danh sách và đánh giá từ Observation.\n"
                "Final Answer: Machine Learning for Everybody có điểm 4.7/5 với 12,500 lượt đánh giá. "
                "Ưu điểm là dễ hiểu và miễn phí; nhược điểm là phần toán nhanh và ít bài tập có chấm điểm."
            )

        if "observation:" in text and "data analysis" in text:
            return (
                "Thought: Đã nhận được danh sách khóa học từ Observation.\n"
                "Final Answer: Đã tìm thấy 3 khóa học Data Analysis gồm Google Data Analytics Professional Certificate, "
                "Data Analysis with Python và The Complete Data Analyst Bootcamp."
            )

        if "machine learning" in text and "observation:" not in text:
            return (
                "Thought: Cần tìm danh sách khóa học Machine Learning trước.\n"
                "Action: search_online_courses[Machine Learning]"
            )

        if "review" in text or "đánh giá" in text:
            return (
                "Thought: Cần tra cứu review khóa học cụ thể.\n"
                "Action: get_course_reviews[Machine Learning for Everybody]"
            )

        if "data analysis" in text or "data analytics" in text:
            return (
                "Thought: Cần tra cứu danh sách khóa học Data Analysis.\n"
                "Action: search_online_courses[Data Analysis]"
            )

        if "python" in text:
            return (
                "Final Answer: Khi bắt đầu Python, hãy tập trung vào cú pháp và kiểu dữ liệu, "
                "điều khiển luồng, hàm, cấu trúc dữ liệu, xử lý lỗi, module và luyện tập bằng dự án nhỏ."
            )

        if "online" in text and "offline" in text:
            return (
                "Final Answer: Học online linh hoạt, tiết kiệm thời gian và có nhiều tài liệu; "
                "đổi lại cần tự giác và ít tương tác trực tiếp hơn học offline. "
                "Học offline có lịch cố định, phản hồi nhanh và môi trường kỷ luật hơn nhưng kém linh hoạt."
            )

        return "Final Answer: Tôi có thể tư vấn lộ trình học tập dựa trên kiến thức chung."


def get_llm_provider(provider_name: str = None) -> BaseLLMProvider:
    """Factory function tự chọn Provider từ biến môi trường LLM_PROVIDER"""
    name = (provider_name or os.getenv("LLM_PROVIDER") or "mock").lower().strip()

    # Chạy lab phải deterministic và không phụ thuộc mạng nếu người dùng chưa
    # cấu hình credential hợp lệ, kể cả khi máy có LLM_PROVIDER toàn cục.
    key_by_provider = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "gemini": os.getenv("GEMINI_API_KEY"),
        "anthropic": os.getenv("ANTHROPIC_API_KEY"),
        "openrouter": os.getenv("OPENROUTER_API_KEY"),
    }
    if name in key_by_provider and not key_by_provider[name]:
        return MockProvider()
    
    if name == "gemini":
        return GeminiProvider()
    elif name == "openai":
        return OpenAIProvider()
    elif name == "anthropic":
        return AnthropicProvider()
    elif name == "openrouter":
        return OpenRouterProvider()
    else:
        return MockProvider()


if __name__ == "__main__":
    print("=== TEST MULTI-PROVIDER LLM ADAPTER ===")
    provider = get_llm_provider()
    print(f"✅ Provider đang dùng: {provider.__class__.__name__}")
    print(f"🤖 User Query: Hello")
    print(f"💬 Response  : {provider.generate('Hello')}")
