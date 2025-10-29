/**
 * Tests for Toast component and provider
 */

import { render, screen, waitFor } from "@testing-library/react";
import { ToastProvider, useToast } from "@/components/Toast";

describe("Toast Component", () => {
  // Test component that uses the hook
  function TestComponent() {
    const { push } = useToast();

    return (
      <div>
        <button onClick={() => push("Test message")}>Show Toast</button>
        <button onClick={() => push("Success!", "success")}>
          Show Success
        </button>
        <button onClick={() => push("Error!", "error")}>Show Error</button>
      </div>
    );
  }

  it("renders toast provider without errors", () => {
    render(
      <ToastProvider>
        <div>Test content</div>
      </ToastProvider>
    );
    expect(screen.getByText("Test content")).toBeInTheDocument();
  });

  it("displays toast message when push is called", () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const button = screen.getByText("Show Toast");
    button.click();

    expect(screen.getByText("Test message")).toBeInTheDocument();
  });

  it("auto-dismisses toast after 4 seconds", async () => {
    jest.useFakeTimers();

    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    const button = screen.getByText("Show Toast");
    button.click();

    // Toast should be visible immediately
    expect(screen.getByText("Test message")).toBeInTheDocument();

    // Fast-forward time by 4 seconds
    jest.advanceTimersByTime(4000);

    // Toast should be gone
    await waitFor(() => {
      expect(screen.queryByText("Test message")).not.toBeInTheDocument();
    });

    jest.useRealTimers();
  });

  it("supports different toast types", () => {
    const { container } = render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    // Show success toast
    screen.getByText("Show Success").click();
    const successToast = screen.getByText("Success!");
    expect(successToast.parentElement?.className).toContain("bg-green-600");

    // Show error toast
    screen.getByText("Show Error").click();
    const errorToast = screen.getByText("Error!");
    expect(errorToast.parentElement?.className).toContain("bg-red-600");
  });

  it("handles multiple toasts simultaneously", () => {
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );

    // Show multiple toasts
    screen.getByText("Show Toast").click();
    screen.getByText("Show Success").click();
    screen.getByText("Show Error").click();

    // All should be visible
    expect(screen.getByText("Test message")).toBeInTheDocument();
    expect(screen.getByText("Success!")).toBeInTheDocument();
    expect(screen.getByText("Error!")).toBeInTheDocument();
  });

  it("throws error when useToast is used outside provider", () => {
    // Suppress console.error for this test
    const consoleError = jest
      .spyOn(console, "error")
      .mockImplementation(() => {});

    function InvalidComponent() {
      const { push } = useToast();
      return <button onClick={() => push("test")}>Test</button>;
    }

    expect(() => {
      render(<InvalidComponent />);
    }).toThrow("useToast must be used within ToastProvider");

    consoleError.mockRestore();
  });
});
