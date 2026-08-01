import { NextRequest } from "next/server";
import {
  calculateCost,
  ChatMessage,
  estimateTokens,
  getServerModelConfig,
  ModelConfig,
} from "@/lib/models";

export const runtime = "nodejs";

type ChatBody = {
  prompt: string;
  config: ModelConfig;
  memory: ChatMessage[];
};

type OpenAIUsage = {
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
};

const encoder = new TextEncoder();

function encodeEvent(type: string, data: unknown) {
  return encoder.encode(`event: ${type}\ndata: ${JSON.stringify(data)}\n\n`);
}

function sleep(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function getModelId(config: ModelConfig) {
  const serverConfig = getServerModelConfig();
  return config.label.includes("Economy")
    ? serverConfig.economy.modelId
    : serverConfig.premium.modelId;
}

function toOpenAIMessages(memory: ChatMessage[], prompt: string, systemPrompt: string) {
  return [
    { role: "system", content: systemPrompt },
    ...memory
      .filter((message) => message.role !== "system")
      .map((message) => ({ role: message.role, content: message.content })),
    { role: "user", content: prompt },
  ];
}

async function streamMock(controller: ReadableStreamDefaultController, body: ChatBody) {
  const startedAt = performance.now();
  const modelId = getModelId(body.config);
  let firstTokenAt: number | null = null;
  const text =
    body.config.label.includes("Economy")
      ? `Bản Economy dùng ${modelId}: trả lời ngắn, nhanh và rẻ hơn cho câu hỏi "${body.prompt}".`
      : `Bản Premium dùng ${modelId}: phân tích kỹ hơn cho câu hỏi "${body.prompt}", thường chậm hơn và tốn chi phí cao hơn nhưng phù hợp tác vụ cần lập luận tốt.`;

  for (const piece of text.match(/.{1,10}/g) ?? []) {
    if (firstTokenAt === null) firstTokenAt = performance.now();
    controller.enqueue(encodeEvent("token", { delta: piece }));
    await sleep(body.config.label.includes("Economy") ? 30 : 60);
  }

  const completedAt = performance.now();
  const inputTokens = estimateTokens(body.prompt);
  const outputTokens = estimateTokens(text);
  const cost = calculateCost(inputTokens, outputTokens, body.config);
  controller.enqueue(
    encodeEvent("done", {
      modelId,
      inputTokens,
      outputTokens,
      totalTokens: inputTokens + outputTokens,
      ...cost,
      ttftMs: firstTokenAt ? firstTokenAt - startedAt : null,
      latencyMs: completedAt - startedAt,
      tokensPerSecond: firstTokenAt
        ? outputTokens / Math.max(0.001, (completedAt - firstTokenAt) / 1000)
        : null,
    }),
  );
}

async function streamOpenAI(controller: ReadableStreamDefaultController, body: ChatBody) {
  const apiKey = process.env.OPENAI_API_KEY;
  const baseUrl = process.env.OPENAI_BASE_URL ?? "https://api.openai.com/v1";
  if (!apiKey) {
    await streamMock(controller, body);
    return;
  }

  const startedAt = performance.now();
  const modelId = getModelId(body.config);
  let firstTokenAt: number | null = null;
  let fullText = "";
  let usage: OpenAIUsage = {};

  const response = await fetch(`${baseUrl}/chat/completions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      model: modelId,
      messages: toOpenAIMessages(body.memory, body.prompt, body.config.systemPrompt),
      temperature: body.config.temperature,
      top_p: body.config.topP,
      max_tokens: body.config.maxTokens,
      stream: true,
      stream_options: { include_usage: true },
    }),
  });

  if (!response.ok || !response.body) {
    const detail = await response.text().catch(() => "");
    throw new Error(`OpenAI API error ${response.status}${detail ? `: ${detail.slice(0, 160)}` : ""}`);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed.startsWith("data:")) continue;
      const data = trimmed.slice(5).trim();
      if (data === "[DONE]") continue;

      const parsed = JSON.parse(data);
      if (parsed.usage) usage = parsed.usage;
      const delta = parsed.choices?.[0]?.delta?.content ?? "";
      if (!delta) continue;

      if (firstTokenAt === null) firstTokenAt = performance.now();
      fullText += delta;
      controller.enqueue(encodeEvent("token", { delta }));
    }
  }

  const completedAt = performance.now();
  const inputTokens = usage.prompt_tokens ?? estimateTokens(body.prompt);
  const outputTokens = usage.completion_tokens ?? estimateTokens(fullText);
  const cost = calculateCost(inputTokens, outputTokens, body.config);
  controller.enqueue(
    encodeEvent("done", {
      modelId,
      inputTokens,
      outputTokens,
      totalTokens: usage.total_tokens ?? inputTokens + outputTokens,
      ...cost,
      ttftMs: firstTokenAt ? firstTokenAt - startedAt : null,
      latencyMs: completedAt - startedAt,
      tokensPerSecond: firstTokenAt
        ? outputTokens / Math.max(0.001, (completedAt - firstTokenAt) / 1000)
        : null,
    }),
  );
}

export async function POST(request: NextRequest) {
  const body = (await request.json()) as ChatBody;
  if (!body.prompt?.trim()) {
    return Response.json({ error: "Prompt is required" }, { status: 400 });
  }
  if (body.prompt.length > 8000) {
    return Response.json({ error: "Prompt is too long" }, { status: 413 });
  }

  const stream = new ReadableStream({
    async start(controller) {
      try {
        await streamOpenAI(controller, body);
      } catch (error) {
        controller.enqueue(
          encodeEvent("error", {
            message: error instanceof Error ? error.message : "Unknown error",
          }),
        );
      } finally {
        controller.close();
      }
    },
  });

  return new Response(stream, {
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      Connection: "keep-alive",
    },
  });
}
