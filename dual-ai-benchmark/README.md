# Dual AI Chatbot Benchmark

Ứng dụng Next.js đơn giản để so sánh hai model OpenAI song song.

## Model mặc định

- Model A, Economy: `gpt-4o-mini`
- Model B, Premium: `gpt-4o`

Hai model này chênh lệch rõ về chi phí và năng lực. `gpt-4o-mini` phù hợp workload rẻ, nhanh; `gpt-4o` phù hợp câu hỏi cần chất lượng cao hơn.

## Tính năng

- Nhập một câu hỏi, gửi đồng thời đến hai model.
- Streaming riêng cho từng cột.
- Một model lỗi không làm dừng model còn lại.
- Memory độc lập, tối đa 10 lượt cho mỗi model.
- Chỉnh trực tiếp `temperature`, `topP`, `topK`, `maxTokens`.
- Với OpenAI Chat Completions, `topK` không được gửi lên API vì không hỗ trợ.
- Đo TTFT, total latency, tokens/s.
- Ước tính input token, output token và chi phí USD.
- Lưu trạng thái vào `localStorage`.
- Chạy mock streaming khi chưa có `OPENAI_API_KEY`.

## Kiến trúc

```text
app/page.tsx              UI dashboard, gọi hai stream song song
app/api/chat/route.ts     Backend API route, gọi OpenAI và giữ API key phía server
lib/models.ts             Model config, type, tính token/cost
.env.example              Biến môi trường mẫu
```

Luồng xử lý:

```text
User prompt
  -> frontend tạo 2 request độc lập
  -> POST /api/chat cho Economy và Premium cùng lúc
  -> API route gọi OpenAI Chat Completions streaming hoặc mock fallback
  -> frontend đọc SSE, cập nhật từng cột
  -> lưu memory riêng từng model vào localStorage
```

## Cài đặt

```bash
npm install
cp .env.example .env.local
npm run dev
```

Mở `http://localhost:3000` hoặc port mà Next hiển thị.

Nếu chưa có API key, app tự chạy dữ liệu mẫu để demo streaming.

## Cấu hình OpenAI API

Điền vào `.env.local`:

```env
OPENAI_API_KEY=sk-...
OPENAI_BASE_URL=https://api.openai.com/v1
MODEL_A_ID=gpt-4o-mini
MODEL_B_ID=gpt-4o
```

Config mặc định nằm trong `lib/models.ts`. Khi muốn đổi model, sửa `MODEL_A_ID`, `MODEL_B_ID` trong `.env.local` và cập nhật giá trong `lib/models.ts` nếu cần.

## Ghi chú bảo mật

- API key chỉ được đọc trong API route phía server.
- Frontend không nhận hoặc log API key.
- Prompt quá dài bị chặn ở 8.000 ký tự.
- Khi API lỗi, lỗi được hiển thị trong cột tương ứng.

## Kiểm tra

```bash
npm run build
```
