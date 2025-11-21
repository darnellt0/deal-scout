"use client";
import { useEffect } from "react";

const DEMO_MODE_KEY = "deal-scout-demo-mode";
const STORAGE_KEY = "auth_token";

export function DemoInitializer() {
  useEffect(() => {
    if (typeof window === "undefined") return;

    const initDemo = async () => {
      try {
        const demoModeEnabled =
          window.localStorage.getItem(DEMO_MODE_KEY) !== "false";

        if (!demoModeEnabled) {
          return;
        }

        const existingToken = window.localStorage.getItem(STORAGE_KEY);
        if (existingToken) {
          // Set the cookie if we already have a token
          window.document.cookie = `Authorization=Bearer ${existingToken}; path=/; SameSite=Lax`;
          return;
        }

        try {
          const loginResponse = await fetch("/api/proxy/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              username: "demo",
              password: "demo123456",
            }),
          });

          if (loginResponse.ok) {
            const data = await loginResponse.json();
            if (data.access_token) {
              window.localStorage.setItem(STORAGE_KEY, data.access_token);
              // Set the cookie so the proxy can read it
              window.document.cookie = `Authorization=Bearer ${data.access_token}; path=/; SameSite=Lax`;
              window.location.reload();
              return;
            }
          }
        } catch (loginError) {
          // Fall through to registration
        }

        try {
          const registerResponse = await fetch("/api/proxy/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              username: "demo",
              email: "demo@example.com",
              password: "demo123456",
              first_name: "Demo",
              last_name: "User",
            }),
          });

          if (registerResponse.ok) {
            const data = await registerResponse.json();
            if (data.access_token) {
              window.localStorage.setItem(STORAGE_KEY, data.access_token);
              // Set the cookie so the proxy can read it
              window.document.cookie = `Authorization=Bearer ${data.access_token}; path=/; SameSite=Lax`;
              window.location.reload();
              return;
            }
          }
        } catch (registerError) {
          // Registration also failed
        }
      } catch (error) {
        // Silently fail
      }
    };

    initDemo();
  }, []);

  return null;
}
