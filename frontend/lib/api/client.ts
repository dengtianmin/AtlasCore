import { getAdminToken } from "@/lib/auth/token";

const DEFAULT_API_BASE_URL = process.env.NEXT_PUBLIC_ATLASCORE_API_BASE_URL || "http://127.0.0.1:8000";

export class ApiError extends Error {
  status: number;
  detail: string;

  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

type RequestOptions = {
  method?: string;
  body?: BodyInit | object | null;
  token?: string;
  headers?: HeadersInit;
};

type StreamEvent = {
  event: string;
  data: unknown;
};

type StreamRequestOptions = RequestOptions & {
  onEvent: (event: StreamEvent) => void;
};

function resolveHeaders(body: RequestOptions["body"], token?: string, headers?: HeadersInit) {
  const merged = new Headers(headers);

  if (token) {
    merged.set("Authorization", `Bearer ${token}`);
  }

  if (body && !(body instanceof FormData) && !merged.has("Content-Type")) {
    merged.set("Content-Type", "application/json");
  }

  return merged;
}

function resolveBody(body: RequestOptions["body"]) {
  if (!body) {
    return undefined;
  }
  if (body instanceof FormData) {
    return body;
  }
  if (typeof body === "string" || body instanceof Blob) {
    return body;
  }
  return JSON.stringify(body);
}

async function parseError(response: Response) {
  try {
    const payload = await response.json();
    if (payload.detail) {
      return String(payload.detail);
    }
  } catch {
    return response.statusText || "请求失败";
  }
  return response.statusText || "请求失败";
}

function parseEventBlock(block: string): StreamEvent | null {
  const lines = block.split(/\r?\n/);
  let eventName = "message";
  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim() || "message";
      continue;
    }
    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trimStart());
    }
  }

  if (!dataLines.length) {
    return null;
  }

  const rawData = dataLines.join("\n");
  return {
    event: eventName,
    data: JSON.parse(rawData)
  };
}

export async function requestJson<T>(path: string, options: RequestOptions = {}) {
  const token = options.token ?? getAdminToken();
  const response = await fetch(`${DEFAULT_API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: resolveHeaders(options.body, token, options.headers),
    body: resolveBody(options.body),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response));
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

export async function requestBlob(path: string, options: RequestOptions = {}) {
  const token = options.token ?? getAdminToken();
  const response = await fetch(`${DEFAULT_API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: resolveHeaders(options.body, token, options.headers),
    body: resolveBody(options.body),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response));
  }

  return response.blob();
}

export async function requestEventStream(path: string, options: StreamRequestOptions) {
  const token = options.token ?? getAdminToken();
  const response = await fetch(`${DEFAULT_API_BASE_URL}${path}`, {
    method: options.method ?? "GET",
    headers: resolveHeaders(options.body, token, options.headers),
    body: resolveBody(options.body),
    cache: "no-store"
  });

  if (!response.ok) {
    throw new ApiError(response.status, await parseError(response));
  }

  if (!response.body) {
    throw new ApiError(500, "流式响应为空");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value || new Uint8Array(), { stream: !done });

    const blocks = buffer.split(/\r?\n\r?\n/);
    buffer = blocks.pop() || "";

    for (const block of blocks) {
      const parsed = parseEventBlock(block);
      if (parsed) {
        options.onEvent(parsed);
      }
    }

    if (done) {
      break;
    }
  }

  if (buffer.trim()) {
    const parsed = parseEventBlock(buffer);
    if (parsed) {
      options.onEvent(parsed);
    }
  }
}
