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

  it("throws readable API errors when response includes error detail", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 401,
      json: async () => ({ detail: "Unauthorized" }),
    }) as unknown as typeof fetch;

    const { getTrucks } = await import("@/lib/api");

    await expect(getTrucks()).rejects.toThrow("Unauthorized");
    await expect(getTrucks()).rejects.toMatchObject({ status: 401 });
  });

  it("falls back to status when API error body is unreadable", async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("invalid json");
      },
    }) as unknown as typeof fetch;

    const { getTrucks } = await import("@/lib/api");

    await expect(getTrucks()).rejects.toThrow("API request failed: 500");
  });

  it("fetches live positions with authenticated request", async () => {
    const { getLivePositions } = await import("@/lib/api");

    await getLivePositions();

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/fleet/live-positions",
      expect.any(Object),
    );

    const [, options] = vi.mocked(global.fetch).mock.calls[0];
    const headers = options?.headers as Headers;

    expect(headers.get("Authorization")).toBe("Bearer test-firebase-token");
  });

  it("fetches dispatcher command-center decisions with authenticated request", async () => {
    const { getDispatcherDecision } = await import("@/lib/api");

    await getDispatcherDecision("LOAD-1");

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/dispatcher-command-center/loads/LOAD-1/decision",
      expect.any(Object),
    );

    const [, options] = vi.mocked(global.fetch).mock.calls[0];
    const headers = options?.headers as Headers;

    expect(headers.get("Authorization")).toBe("Bearer test-firebase-token");
  });

  it("accepts dispatcher recommendations with authenticated JSON request", async () => {
    const { acceptDispatcherRecommendation } = await import("@/lib/api");

    await acceptDispatcherRecommendation("LOAD-1", "TRUCK-1", "DRIVER-1");

    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/dispatcher-command-center/loads/LOAD-1/assign",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({
          truck_id: "TRUCK-1",
          driver_id: "DRIVER-1",
        }),
      }),
    );

    const [, options] = vi.mocked(global.fetch).mock.calls[0];
    const headers = options?.headers as Headers;

    expect(headers.get("Authorization")).toBe("Bearer test-firebase-token");
    expect(headers.get("Content-Type")).toBe("application/json");
  });
});

describe("carrier API functions", () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();

    process.env.NEXT_PUBLIC_API_URL = "http://localhost:8000";
    mockGetIdToken.mockResolvedValue("test-firebase-token");

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    }) as unknown as typeof fetch;
  });

  it("listCarriers with no params hits /api/carriers with no query string", async () => {
    const { listCarriers } = await import("@/lib/api");
    await listCarriers();
    expect(global.fetch).toHaveBeenCalledWith(
      "http://localhost:8000/api/carriers",
      expect.any(Object),
    );
  });

  it("listCarriers serializes only defined, non-empty filter params", async () => {
    const { listCarriers } = await import("@/lib/api");
    await listCarriers({
      state: "TX",
      power_units_min: 5,
      authority_status: "",
      order_by: "authority_date_desc",
    });
    const [url] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toContain("state=TX");
    expect(url).toContain("power_units_min=5");
    expect(url).toContain("order_by=authority_date_desc");
    expect(url).not.toContain("authority_status");
  });

  it("searchCarriers builds correct URL with q, page, and page_size", async () => {
    const { searchCarriers } = await import("@/lib/api");
    await searchCarriers("ACME Freight", 2, 25);
    const [url] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toContain("/api/carriers/search");
    expect(url).toContain("q=ACME+Freight");
    expect(url).toContain("page=2");
    expect(url).toContain("page_size=25");
  });

  it("updateOutreachStatus sends PATCH with JSON body", async () => {
    const { updateOutreachStatus } = await import("@/lib/api");
    await updateOutreachStatus(42, "contacted");
    const [url, options] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/carriers/42/outreach-status");
    expect(options?.method).toBe("PATCH");
    expect(options?.body).toBe(JSON.stringify({ status: "contacted" }));
  });

  it("createNote POSTs with required content and omits undefined optional fields", async () => {
    const { createNote } = await import("@/lib/api");
    await createNote(7, { content: "Called dispatcher" });
    const [url, options] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/carriers/7/notes");
    expect(options?.method).toBe("POST");
    const body = JSON.parse(options?.body as string);
    expect(body.content).toBe("Called dispatcher");
    expect(body).not.toHaveProperty("outcome");
    expect(body).not.toHaveProperty("follow_up_date");
  });

  it("deleteNote sends DELETE to the correct URL", async () => {
    const { deleteNote } = await import("@/lib/api");
    await deleteNote(7, 99);
    const [url, options] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/carriers/7/notes/99");
    expect(options?.method).toBe("DELETE");
  });

  it("removeTagFromCarrier sends DELETE to the correct URL", async () => {
    const { removeTagFromCarrier } = await import("@/lib/api");
    await removeTagFromCarrier(7, 3);
    const [url, options] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/carriers/7/tags/3");
    expect(options?.method).toBe("DELETE");
  });

  it("createTag POSTs the tag name", async () => {
    const { createTag } = await import("@/lib/api");
    await createTag("hotshot");
    const [url, options] = vi.mocked(global.fetch).mock.calls[0];
    expect(url).toBe("http://localhost:8000/api/tags");
    expect(options?.method).toBe("POST");
    expect(JSON.parse(options?.body as string)).toEqual({ name: "hotshot" });
  });
});
