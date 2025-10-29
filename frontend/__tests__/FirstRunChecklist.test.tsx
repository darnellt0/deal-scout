/**
 * Tests for FirstRunChecklist component
 */

import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import FirstRunChecklist from "@/components/FirstRunChecklist";
import { ToastProvider } from "@/components/Toast";

// Mock fetch
global.fetch = jest.fn();

describe("FirstRunChecklist Component", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
  });

  const mockStatusResponse = {
    ok: false,
    checks: [
      {
        id: "db",
        label: "Database connected",
        status: "ok",
        details: "PostgreSQL reachable",
      },
      {
        id: "redis",
        label: "Redis connected",
        status: "ok",
        details: "Redis PING successful",
      },
      {
        id: "worker",
        label: "Background worker running",
        status: "warn",
        details: "No response within 2s",
      },
    ],
    progress: 0.67,
    timestamp: "2025-10-28T16:00:00Z",
  };

  const mockDismissedResponse = {
    dismissed: false,
    dismissed_at: null,
  };

  it("renders banner when status is not ok and not dismissed", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    await waitFor(() => {
      expect(
        screen.getByText("Let's finish setup")
      ).toBeInTheDocument();
    });
  });

  it("hides banner when dismissed", async () => {
    const dismissedResponse = { dismissed: true, dismissed_at: null };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => dismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    await waitFor(() => {
      expect(
        screen.queryByText("Let's finish setup")
      ).not.toBeInTheDocument();
    });
  });

  it("displays correct progress percentage", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    await waitFor(() => {
      // 0.67 * 100 = 67%
      expect(screen.getByText("67%")).toBeInTheDocument();
    });
  });

  it("displays check status with correct icons", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    await waitFor(() => {
      // Check that labels are displayed
      expect(screen.getByText("Database connected")).toBeInTheDocument();
      expect(screen.getByText("Redis connected")).toBeInTheDocument();
      expect(screen.getByText("Background worker running")).toBeInTheDocument();
    });
  });

  it("calls run live scan endpoint when button is clicked", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          mode: "blocking",
          live: true,
          total: 5,
          new: 2,
          updated: 1,
          skipped: 0,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    const scanButton = await screen.findByText("Run live scan now");
    fireEvent.click(scanButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith("/scan/run?live=1&blocking=1", {
        method: "POST",
      });
    });
  });

  it("shows success toast after successful scan", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          mode: "blocking",
          live: true,
          total: 5,
          new: 2,
          updated: 1,
          skipped: 0,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    const scanButton = await screen.findByText("Run live scan now");
    fireEvent.click(scanButton);

    await waitFor(() => {
      expect(
        screen.getByText("Live scan complete: 2 new, 1 updated, 5 total.")
      ).toBeInTheDocument();
    });
  });

  it("shows error toast when scan fails", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      })
      .mockResolvedValueOnce({
        ok: false,
        status: 500,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    const scanButton = await screen.findByText("Run live scan now");
    fireEvent.click(scanButton);

    await waitFor(() => {
      expect(screen.getByText(/Scan failed:/)).toBeInTheDocument();
    });
  });

  it("disables scan button while scanning", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      })
      .mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ok: true,
                  json: async () => ({
                    mode: "blocking",
                    live: true,
                    total: 5,
                    new: 2,
                    updated: 1,
                  }),
                }),
              100
            )
          )
      )
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    const scanButton = await screen.findByText("Run live scan now");
    fireEvent.click(scanButton);

    // Button should show loading state
    await waitFor(() => {
      expect(screen.getByText("Scanning...")).toBeInTheDocument();
    });
  });

  it("dismisses banner when dismiss button is clicked", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({}),
      });

    const { container } = render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    // Find and click the close button (X)
    const closeButton = container.querySelector(
      "button[title='Dismiss banner']"
    );
    expect(closeButton).toBeInTheDocument();

    fireEvent.click(closeButton!);

    await waitFor(() => {
      expect(
        screen.queryByText("Let's finish setup")
      ).not.toBeInTheDocument();
    });
  });

  it("hides automatically when progress >= 95%", async () => {
    const almostCompleteResponse = { ...mockStatusResponse, progress: 0.95 };

    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => almostCompleteResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    await waitFor(() => {
      expect(
        screen.queryByText("Let's finish setup")
      ).not.toBeInTheDocument();
    });
  });

  it("sets demoMode to 'off' in localStorage when running live scan", async () => {
    (global.fetch as jest.Mock)
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockDismissedResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          mode: "blocking",
          live: true,
          total: 0,
          new: 0,
          updated: 0,
          skipped: 0,
        }),
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatusResponse,
      });

    render(
      <ToastProvider>
        <FirstRunChecklist />
      </ToastProvider>
    );

    const scanButton = await screen.findByText("Run live scan now");
    fireEvent.click(scanButton);

    await waitFor(() => {
      expect(localStorage.getItem("demoMode")).toBe("off");
    });
  });
});
