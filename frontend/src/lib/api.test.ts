import { beforeEach, describe, expect, it, vi } from "vitest";

const mockGetIdToken = vi.fn();

vi.mock("@/lib/firebase", () => ({
  auth: {
    currentUser: {
      getIdToken: mockGetIdToken,
    },
  },
}));

describe("api client", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();

    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
    process.env.INTERNAL_API_URL = "http://api:8000";

    mockGetIdToken.mockResolvedValue("test-firebase-token");

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    }) as unknown as typeof fetch;
  });

  it("uses NEXT_PUBLIC_API_URL before INTERNAL_API_URL", async () => {
    const { getTrucks } = await import("@/lib/api");

    await getTrucks();

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/trucks",
      expect.any(Object),
    );
  });

  it("adds Firebase bearer token to requests", async () => {
    const { getTrucks } = await import("@/lib/api");

    await getTrucks();

    const [, options] = vi.mocked(global.fetch).mock.calls[0];
    const headers = options?.headers as Headers;

    expect(headers.get("Authorization")).toBe("Bearer test-firebase-token");
  });

  it("throws when API response is not ok", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Unauthorized" }),
    }) as unknown as typeof fetch;

    const { getTrucks } = await import("@/lib/api");

    await expect(getTrucks()).rejects.toThrow("API request failed: 401");
  });
});
