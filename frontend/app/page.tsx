"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    // Check if user is logged in
    const token = localStorage.getItem("auth_token");

    if (!token) {
      // Not logged in, redirect to login
      router.push("/login");
    } else {
      // Logged in, check role and redirect
      const userStr = localStorage.getItem("user");
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          if (user.role === "seller") {
            router.push("/seller");
          } else {
            router.push("/buyer");
          }
        } catch {
          // Invalid user data, redirect to login
          router.push("/login");
        }
      } else {
        router.push("/login");
      }
    }
  }, [router]);

  return (
    <div className="flex items-center justify-center min-h-screen">
      <p className="text-slate-500">Loading...</p>
    </div>
  );
}
