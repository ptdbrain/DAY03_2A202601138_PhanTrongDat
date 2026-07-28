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
from tools import call_tool
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


def run_baseline_chatbot(user_query: str, provider, verbose: bool = True):
    """
    Dựng Chatbot gốc (Baseline) không có công cụ.
    """
    if verbose:
        print(f"\n💬 [CHATBOT BASELINE] Câu hỏi: {user_query}")
        print(f"⚙️ System Prompt: {CHATBOT_BASELINE_PROMPT.strip()}")
    
    # Gọi LLM Provider thực hiện sinh câu trả lời
    response = provider.generate(user_query, system_prompt=CHATBOT_BASELINE_PROMPT)
    if verbose:
        print(f"🤖 Chatbot trả lời:\n{response}")
    return {
        "answer": response,
        "tool_calls": [],
        "termination": "final",
        "trace": [{"type": "final", "content": response}],
    }


def _grounded_fallback(trace: list, limit: int) -> tuple[str, str]:
    """Return a safe answer from tool evidence if the LLM never finalizes."""
    observations = []
    seen = set()
    for item in trace:
        if item.get("type") != "observation":
            continue
        content = str(item.get("content", "")).strip()
        if not content or content in seen:
            continue
        seen.add(content)
        observations.append(content)

    refusals = [item for item in observations if item.upper().startswith("TỪ CHỐI:")]
    if refusals:
        return refusals[0], "refusal"

    useful = [item for item in observations if not item.upper().startswith("LỖI")]
    if useful:
        return (
            f"Đã chạm giới hạn {limit} bước, nhưng tôi đã tra cứu được "
            "các thông tin sau từ công cụ:\n\n"
            + "\n\n".join(useful),
            "fallback" if len(useful) > 1 else "max_iterations",
        )

    return (
        f"Xin lỗi, tôi chưa thể hoàn tất câu trả lời trong giới hạn {limit} bước cho phép.",
        "max_iterations",
    )


def run_react_agent(user_query: str, provider, max_iterations: int = None, verbose: bool = True):
    """
    Dựng vòng lặp ReAct Agent (Thought -> Action -> Observation) có Guardrails.
    Gọi LLM thật, parse Action, thực thi Tool, append Observation vào prompt.
    """
    import re

    limit = MAX_ITERATIONS if max_iterations is None else max_iterations
    trace = []
    tool_calls = []
    conversation = f"Question: {user_query}\n"
    final_answer = None
    termination = "max_iterations"

    if verbose:
        print(f"\n🤖 [REACT AGENT] Câu hỏi: {user_query}")

    for step in range(1, limit + 1):
        if verbose:
            print(f"\n--- 🔄 Vòng lặp ReAct (Step {step}/{limit}) ---")
        llm_output = provider.generate(conversation, system_prompt=REACT_SYSTEM_PROMPT)
        trace.append({"type": "llm", "step": step, "content": llm_output})
        if verbose:
            print(f"📤 LLM Output:\n{llm_output}")

        final_match = re.search(r"Final Answer:\s*(.+)", llm_output, re.DOTALL | re.IGNORECASE)
        if final_match:
            final_answer = final_match.group(1).strip()
            termination = "refusal" if final_answer.upper().startswith("TỪ CHỐI") else "final"
            trace.append({"type": "final", "step": step, "content": final_answer})
            if verbose:
                print(f"\n🏁 Final Answer: {final_answer}")
            break

        action_match = re.search(r"Action:\s*([A-Za-z_][\w]*)\s*\[(.*?)\]", llm_output, re.DOTALL)
        if action_match:
            tool_name = action_match.group(1).strip()
            tool_arg = action_match.group(2).strip().strip("'\"").strip()
            tool_calls.append(tool_name)
            trace.append({"type": "action", "step": step, "tool": tool_name, "input": tool_arg})
            if verbose:
                print(f"🛠️ Action: {tool_name}[{tool_arg}]")
            observation = call_tool(tool_name, tool_arg)
            trace.append({"type": "observation", "step": step, "content": observation})
            if verbose:
                print(f"👁️ Observation: {observation}")
            conversation += f"\n{llm_output}\nObservation: {observation}\n"
        else:
            observation = "LỖI: Định dạng không hợp lệ. Hãy dùng Action: tên_tool[tham_số] hoặc Final Answer: câu trả lời."
            trace.append({"type": "observation", "step": step, "content": observation})
            if verbose:
                print(f"⚠️ {observation}")
            conversation += f"\n{llm_output}\nObservation: {observation}\n"

    if final_answer is None:
        final_answer, termination = _grounded_fallback(trace, limit)
        trace.append({"type": "guardrail", "content": final_answer})
        if verbose:
            print(f"\n🛡️ GUARDRAIL TRIGGERED: {final_answer}")

    return {
        "answer": final_answer,
        "tool_calls": tool_calls,
        "termination": termination,
        "trace": trace,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("🏫 ĐẠI HỌC VINUNI - BÀI LAB 3: CHATBOT VS REACT AGENT")
    print("=" * 60)
    
    # Khởi tạo Multi-Provider LLM Adapter (Đọc từ biến môi trường LLM_PROVIDER)
    # Demo/chấm điểm phải chạy offline deterministic. Muốn dùng API thật,
    # đặt DAY03_LIVE_LLM=1 cùng LLM_PROVIDER và credential tương ứng.
    provider_name = os.getenv("LLM_PROVIDER") if os.getenv("DAY03_LIVE_LLM") == "1" else "mock"
    provider = get_llm_provider(provider_name)
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

