"""
🚀 CORE AGENT APP (Dành cho Role 4: Core Agent Developer)
File chính ghép nối tất cả các thành phần: Tools + Prompts + Test Cases + Multi-Provider.
"""

import json
import os
import sys
from dotenv import load_dotenv

# Đảm bảo import các module cùng thư mục src/ hoạt động mượt mà
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Đảm bảo in ra Tiếng Việt và Emojis không bị lỗi trên Windows Console
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Import các thành phần từ file của Role 2, Role 3 & Multi-Provider Adapter
from tools import AVAILABLE_TOOLS, search_online_courses, get_course_reviews
from prompts import CHATBOT_BASELINE_PROMPT, REACT_SYSTEM_PROMPT, MAX_ITERATIONS
from providers import get_llm_provider

load_dotenv()

def load_test_cases():
    """Đọc bộ test cases từ config/test_cases.json của Role 1"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "config", "test_cases.json")
    
    # Fallback kiểm tra nếu file ở thư mục hiện tại
    if not os.path.exists(config_path):
        config_path = "test_cases.json"
        
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


def run_baseline_chatbot(user_query: str, provider):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
    print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    print(f"🤖 Chatbot trả lời:\n{response}")


def run_react_agent(user_query: str, provider):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    Gọi LLM thật, parse Action, thực thi Tool, append Observation vào prompt.
    """
    import re

    print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")
    step = 0
    
    # Khởi tạo conversation history với câu hỏi của user
    conversation = f"Question: {user_query}\n"
    
    while step < MAX_ITERATIONS:
        step += 1
        print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{MAX_ITERATIONS}) ---")
        
        # Gọi LLM với system prompt + conversation history hiện tại
        llm_output = provider.generate(conversation, system_prompt=REACT_SYSTEM_PROMPT)
        print(f"📤 LLM Output:\n{llm_output}")
        
        # --- Kiểm tra Final Answer ---
        final_match = re.search(r"Final Answer:\s*(.+)", llm_output, re.DOTALL)
        if final_match:
            final_answer = final_match.group(1).strip()
            print(f"\n🏁 Final Answer: {final_answer}")
            break
        
        # --- Parse Action: tên_tool[tham_số] ---
        action_match = re.search(r"Action:\s*(\w+)\[(.+?)\]", llm_output)
        if action_match:
            tool_name = action_match.group(1).strip()
            tool_arg = action_match.group(2).strip().strip("'\"")
            
            print(f"🛠️ Action: {tool_name}[{tool_arg}]")
            
            # Thực thi tool nếu tồn tại trong AVAILABLE_TOOLS
            if tool_name in AVAILABLE_TOOLS:
                try:
                    observation = AVAILABLE_TOOLS[tool_name](tool_arg)
                except Exception as e:
                    observation = f"LỖI: Tool '{tool_name}' gặp lỗi khi thực thi: {str(e)}"
            else:
                available_names = ", ".join(AVAILABLE_TOOLS.keys())
                observation = f"LỖI: Tool '{tool_name}' không tồn tại. Các tool hợp lệ: [{available_names}]"
            
            print(f"👁️ Observation: {observation}")
            
            # Append kết quả vào conversation history cho bước tiếp theo
            conversation += f"\n{llm_output}\nObservation: {observation}\n"
        else:
            # Không parse được Action cũng không có Final Answer
            print("⚠️ Không parse được Action hoặc Final Answer từ LLM output.")
            conversation += f"\n{llm_output}\nObservation: LỖI: Định dạng không hợp lệ. Hãy dùng đúng format: Action: tên_tool[tham_số] hoặc Final Answer: câu trả lời.\n"
    
    if step >= MAX_ITERATIONS:
        print(f"\n🛡️ GUARDRAIL TRIGGERED: Đã đạt giới hạn tối đa {MAX_ITERATIONS} bước. Ngắt lặp an toàn!")
        print("💬 Xin lỗi, tôi chưa thể hoàn tất câu trả lời trong giới hạn cho phép. Vui lòng thử lại với câu hỏi cụ thể hơn.")


if __name__ == "__main__":
    print("=" * 60)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("=" * 60)
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    provider = get_llm_provider()
    model_name = getattr(provider, "model_name", "Offline Mock Mode")
    print(f"🔌 LLM Provider đang hoạt động: {provider.__class__.__name__} (Model: {model_name})")
    
    tests = load_test_cases()
    print(f"✅ Đã tải thành công {len(tests)} Test Cases từ config/test_cases.json\n")
    
    # ================================================================
    # 📍 MỐC 2: CHẠY CHATBOT BASELINE TRÊN CẢ 5 TEST CASES
    # ================================================================
    print("=" * 60)
    print("📍 MỐC 2: CHẠY CHATBOT BASELINE (Không có Tool)")
    print("=" * 60)
    
    for i, test in enumerate(tests):
        print(f"\n{'─' * 60}")
        print(f"📝 Test Case #{test['id']} | {test['category']}")
        print(f"❓ Câu hỏi: {test['question']}")
        print(f"🎯 Kỳ vọng: {test['expected_behavior']}")
        print(f"{'─' * 60}")
        
        run_baseline_chatbot(test["question"], provider)
        
        print(f"\n🔢 Tool calls: 0 (Baseline không gọi tool)")

    # ================================================================
    # 📍 MỐC 3: CHẠY REACT AGENT TRÊN CẢ 5 TEST CASES (+ GUARDRAIL)
    # ================================================================
    print(f"\n\n{'=' * 60}")
    print("📍 MỐC 3: CHẠY REACT AGENT (Thought -> Action -> Observation)")
    print("=" * 60)
    
    for test in tests:
        print(f"\n{'═' * 60}")
        print(f"📝 Test Case #{test['id']} | {test['category']}")
        print(f"❓ Câu hỏi: {test['question']}")
        print(f"🎯 Kỳ vọng: {test['expected_behavior']}")
        print(f"{'═' * 60}")
        
        run_react_agent(test["question"], provider)
        
        print(f"\n{'─' * 60}")

