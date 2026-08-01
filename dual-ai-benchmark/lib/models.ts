export type ChatRole = "system" | "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  createdAt: number;
};

export type ModelConfig = {
  label: string;
  provider: string;
  modelId: string;
  temperature: number;
  topP: number;
  topK: number | null;
  maxTokens: number;
  inputPricePerMillion: number;
  outputPricePerMillion: number;
  systemPrompt: string;
};

export type ModelPairConfig = {
  economy: ModelConfig;
  premium: ModelConfig;
};

export type StreamMetrics = {
  modelId?: string;
  inputTokens: number;
  outputTokens: number;
  totalTokens: number;
  inputCost: number;
  outputCost: number;
  totalCost: number;
  ttftMs: number | null;
  latencyMs: number;
  tokensPerSecond: number | null;
};

export type ModelState = {
  config: ModelConfig;
  status: "idle" | "waiting" | "streaming" | "done" | "error" | "stopped";
  response: string;
  error?: string;
  metrics?: StreamMetrics;
  memory: ChatMessage[];
};

export const defaultModels: ModelPairConfig = {
  economy: {
    label: "Model A - Economy",
    provider: "OpenAI",
    modelId: "gpt-4o-mini",
    temperature: 0.7,
    topP: 0.9,
    topK: null,
    maxTokens: 600,
    inputPricePerMillion: 0.15,
    outputPricePerMillion: 0.6,
    systemPrompt:
      "Bạn là trợ lý ngắn gọn, rõ ràng, trả lời bằng tiếng Việt.",
  },
  premium: {
    label: "Model B - Premium",
    provider: "OpenAI",
    modelId: "gpt-4o",
    temperature: 0.7,
    topP: 0.9,
    topK: null,
    maxTokens: 900,
    inputPricePerMillion: 2.5,
    outputPricePerMillion: 10,
    systemPrompt:
      "Bạn là trợ lý cao cấp, lập luận kỹ, chính xác và trả lời bằng tiếng Việt.",
  },
};

export function getServerModelConfig(): ModelPairConfig {
  return {
    economy: {
      ...defaultModels.economy,
      modelId: process.env.MODEL_A_ID || defaultModels.economy.modelId,
    },
    premium: {
      ...defaultModels.premium,
      modelId: process.env.MODEL_B_ID || defaultModels.premium.modelId,
    },
  };
}

export function estimateTokens(text: string): number {
  return Math.max(1, Math.ceil(text.trim().length / 4));
}

export function calculateCost(
  inputTokens: number,
  outputTokens: number,
  config: ModelConfig,
) {
  const inputCost = (inputTokens / 1_000_000) * config.inputPricePerMillion;
  const outputCost = (outputTokens / 1_000_000) * config.outputPricePerMillion;
  return {
    inputCost,
    outputCost,
    totalCost: inputCost + outputCost,
  };
}
