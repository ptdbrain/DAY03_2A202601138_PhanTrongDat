import { getServerModelConfig } from "@/lib/models";

export const runtime = "nodejs";

export function GET() {
  return Response.json(getServerModelConfig());
}
