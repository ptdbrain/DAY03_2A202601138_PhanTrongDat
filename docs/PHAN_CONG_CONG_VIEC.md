# 📋 SỔ TAY PHÂN CÔNG & CHECKLIST THỰC HÀNH (ZERO-CONFLICT WORKFLOW)

> 💡 **Hướng dẫn**: Mỗi thành viên mở đúng file được phân công trong thư mục dự án và thực hiện checklist theo từng Mốc.

---

## 👥 1. BẢNG PHÂN VAI & FILE ĐẢM NHẬN

| Vai trò (Role)                               | File đảm nhận           | Nhiệm vụ chính                                                                                          | Người đảm nhận  | Mã sinh viên |
| :-------------------------------------------- | :------------------------- | :--------------------------------------------------------------------------------------------------------- | :------------------- | :----------- |
| **Role 1: Product Architect**           | `config/test_cases.json` | Định hướng bài toán & soạn bộ câu test case                                                       | `Phan Trọng Đạt` | `2A202601138` |
| **Role 2: Tool Engineer**               | `src/tools.py`           | Định nghĩa các công cụ (Tools) cho Agent                                                             | `Bế Nguyễn Hà Sơn` | `2A202601454` |
| **Role 3: Prompt Engineer**             | `src/prompts.py`         | Viết ReAct System Prompt & phanh Guardrails                                                               | `Giang Trung Quân` | `2A202601098` |
| **Role 4: Core Developer / Integrator** | `src/app.py`             | **Đầu mối kéo code/file của nhóm (`git pull`), Vibe Code lắp ráp thành App hoàn chỉnh** | `Hồ Lương An` | `2A202601332` |
| **Role 5A: Trace Analyst**               | `docs/trace_eval.md`     | Lập bảng Scoring Matrix & Soi nhật ký Trace Log                                                        | `Phạm Tùng Dương` | `2A202601404` |
| **Role 5B: Flowchart Architect**         | `docs/hybrid_flowchart.mermaid` | Vẽ sơ đồ phân luồng quyết định (Hybrid Flowchart)                                                        | `Nguyễn Thành Vinh` | `2A202601556` |

*Note: Nếu nhóm 6 người, Role 5 tách thành 5A (Trace Analyst) và 5B (Flowchart Architect).*

> 🌟 **VAI TRÒ NÒNG NỐT CỦA ROLE 4 (ĐẦU MỐI LẮP RÁP APP HOÀN CHỈNH)**:
>
> - **Role 4** đóng vai trò là **Tổ trưởng Lắp ráp**: Sau khi các bạn Role 1, 2, 3 đẩy file lên Git, **Role 4 sẽ gõ `git pull`** để gom toàn bộ dữ liệu về máy.
> - **Role 4** sau đó dùng AI (Vibe Code) để kết nối `tools.py`, `prompts.py`, `test_cases.json` vào file `src/app.py`, biến các mảnh ghép thành **một Ứng dụng AI Agent hoàn chỉnh** cho cả nhóm chạy nghiệm thu.

---

## ⏱️ 2. CHECKLIST THỰC HÀNH THEO 4 MỐC

### 📍 MỐC 1: Định hình & Đánh giá độ phù hợp (Agentic Fit) (20 phút)

*Mục tiêu: Chứng minh bài toán này CẦN dùng Agent chứ không chỉ Chatbot.*

- [ ] **Role 1 & Cả nhóm**: **Tự do lựa chọn 1 chủ đề bài toán thực tế** mà nhóm hào hứng nhất (Xem 10 đề tài gợi ý tại: [DANH_SACH_DE_TAI.md](file:///c:/Users/Admin/Documents/VinUni/LabCoachVin/LabKeyCoach/Day-3-Lab-Chatbot-vs-react-agent-E402/docs/DANH_SACH_DE_TAI.md)).
- [ ] **Role 5**: Điền bảng **Scoring Matrix** (chấm 1–5 điểm cho 4 tiêu chí) vào `docs/trace_eval.md`.
- [ ] **Role 2**: Liệt kê tên các công cụ sẽ tạo trong `src/tools.py` phù hợp với chủ đề nhóm đã chọn.
- [ ] **Role 3**: Xác định các trường hợp tool có thể bị lỗi (Failure Modes).
- [ ] **Role 4**: Mở Terminal gõ `python src/app.py` kiểm tra xem môi trường sẵn sàng chưa.
- [ ] 🤝 **Cả nhóm**: Gật đầu thống nhất bài toán trước khi sang Mốc 2.
- [ ] 🔄 **Đồng bộ Git Mốc 1**: Cả nhóm lưu file, đẩy code lên Git: `git add .` ➔ `git commit -m "Moc 1: Scoring Matrix & Dinh hinh"` ➔ `git push`.

---

### 📍 MỐC 2: Baseline Chatbot & Khai báo Tool Specs (30 phút)

*Mục tiêu: Thấy rõ hạn chế của Chatbot gốc và chuẩn hóa công cụ cho Agent.*

- [ ] **Role 1**: Viết bộ **Test Cases** vào file `config/test_cases.json` (câu đơn giản, câu multi-step, câu bẫy).
- [ ] **Role 2**: Dùng AI bổ sung Docstring / Mô tả chuẩn cho các hàm trong `src/tools.py`.
- [ ] **Role 3**: Soạn `CHATBOT_BASELINE_PROMPT` trong file `src/prompts.py`.
- [ ] **Role 4 (Đầu mối Lắp ráp)**: Gõ `git pull` để kéo file của Role 1, 2, 3 về máy ➔ Vibe Code nối `run_baseline_chatbot()` trong `src/app.py` và bấm chạy thử.
- [ ] **Role 5**: Ghi lại phản hồi của Chatbot gốc vào `docs/trace_eval.md` (quan sát xem Chatbot có bị ảo giác/không biết thông tin thực tế không).
- [ ] 🔄 **Đồng bộ Git Mốc 2**: Cả nhóm lưu file, đẩy code lên Git: `git add .` ➔ `git commit -m "Moc 2: Chatbot Baseline & Tool Specs"` ➔ `git push`.

---

### 📍 MỐC 3: ReAct Loop & Safeguards (60 phút)

*Mục tiêu: Dựng ReAct Agent suy luận Thought -> Action và cài phanh an toàn.*

- [ ] **Role 3**: Soạn `REACT_SYSTEM_PROMPT` (ép AI sinh Thought -> Action) và đặt `MAX_ITERATIONS (giới hạn số lần lặp)` trong `src/prompts.py`.
- [ ] **Role 2**: Đảm bảo các hàm trong `src/tools.py` khi gặp lỗi sẽ trả về chuỗi thông báo lỗi chứ không crash code.
- [ ] **Role 4 (Đầu mối Lắp ráp & Vibe App)**: Gõ `git pull` kéo toàn bộ code mới nhất ➔ Vibe Code lắp vòng lặp ReAct Agent Loop hoàn chỉnh trong `src/app.py` và chạy thử nghiệm.
- [ ] **Role 5**: Trích xuất chuỗi `Thought -> Action -> Observation` dán vào `docs/trace_eval.md`.
- [ ] **Role 1**: Kiểm tra xem Agent có vượt qua được câu bẫy (Edge Case) bằng phanh Guardrail hay không.
- [ ] 🔄 **Đồng bộ Git Mốc 3**: Cả nhóm lưu file, đẩy code lên Git: `git add .` ➔ `git commit -m "Moc 3: ReAct Agent Loop & Safeguards"` ➔ `git push`.

---

### 📍 MỐC 4: Tương tác liên nhóm & Hybrid Flowchart (40 phút)

*Mục tiêu: Thử thách khả năng chịu lỗi trước đòn tấn công từ nhóm khác & Chấm chéo linh hoạt.*

> 💡 **HÌNH THỨC TƯƠNG TÁC (Tùy Giảng viên chỉ định)**:
>
> * 🎲 **Hình thức 1 (Gọi ngẫu nhiên)**: Giảng viên gọi ngẫu nhiên một thành viên đại diện trong bất kỳ nhóm nào lên trình chiếu App, phản biện và trả lời câu hỏi bẫy từ các nhóm khác.
> * 🔄 **Hình thức 2 (Chấm chéo nhóm)**: Giảng viên chỉ định 1 bạn đại diện (VD: Role 1 hoặc Role 5) đi sang nhóm khác để "tấn công" (dùng câu bẫy thử nghiệm Agent nhóm bạn) và chấm điểm chéo.

- [ ] ⚔️ **Đội Tấn Công (Đại diện/Học viên được gọi)**: Mang các câu test case của nhóm mình sang "xả" vào Agent của Nhóm bạn để kiểm thử khả năng chịu lỗi.
- [ ] 🛡️ **Đội Phòng Thủ**: Quan sát Agent nhóm mình phản ứng trước câu hỏi của nhóm bạn. Kiểm tra xem Guardrail bảo vệ an toàn không.
- [ ] 📊 **Role 5B (hoặc Role 5)**: Vẽ sơ đồ **Hybrid Flowchart** vào file `docs/hybrid_flowchart.mermaid` thể hiện phân luồng:
  - Câu hỏi đơn giản ➔ Đi đường Chatbot path.
  - Câu hỏi phức tạp ➔ Đi đường ReAct Agent path.
- [ ] 🔄 **Đồng bộ Git Mốc 4 (Hoàn thành)**: Cả nhóm lưu file, đẩy bản hoàn chỉnh lên Git: `git add .` ➔ `git commit -m "Moc 4: Cross Audit & Hybrid Flowchart Hoan thanh"` ➔ `git push`.

---

Vì mỗi thành viên giữ đúng 1 file trong các thư mục riêng (`config/`, `src/`, `docs/`), bạn chỉ cần nhớ quy trình :

**Trước khi gõ code**: Kéo code mới của nhóm về:

```bash
   git pull
```

**Đẩy code lên cho nhóm**:

```bash
   git add .
   git commit -m "Role X: cap nhat noi dung"
   git push
```

*(Nếu push bị chặn do bạn khác push trước: Gõ `git pull` rồi `git push` lại là xong!)*
