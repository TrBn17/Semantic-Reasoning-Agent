"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { cn } from "@/lib/utils";

type RouteTransitionContextValue = {
  isNavigating: boolean;
  pendingHref: string | null;
  beginNavigation: (href?: string | null) => void;
};

const MIN_VISIBLE_MS = 650;
const FAILSAFE_MS = 12_000;

const RouteTransitionContext = createContext<RouteTransitionContextValue | null>(null);

export function RouteTransitionProvider({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const routeKey = `${pathname}?${searchParams.toString()}`;
  const [isNavigating, setIsNavigating] = useState(false);
  const [pendingHref, setPendingHref] = useState<string | null>(null);
  const startedAtRef = useRef<number | null>(null);
  const settledRouteRef = useRef(routeKey);

  const finishNavigation = useCallback(() => {
    const startedAt = startedAtRef.current;
    const elapsed = startedAt ? Date.now() - startedAt : MIN_VISIBLE_MS;
    const remaining = Math.max(MIN_VISIBLE_MS - elapsed, 0);

    window.setTimeout(() => {
      setIsNavigating(false);
      setPendingHref(null);
      startedAtRef.current = null;
    }, remaining);
  }, []);

  const beginNavigation = useCallback((href?: string | null) => {
    startedAtRef.current = Date.now();
    setPendingHref(href ?? null);
    setIsNavigating(true);
  }, []);

  useEffect(() => {
    if (!isNavigating) {
      settledRouteRef.current = routeKey;
      return;
    }

    if (routeKey !== settledRouteRef.current) {
      settledRouteRef.current = routeKey;
      finishNavigation();
    }
  }, [finishNavigation, isNavigating, routeKey]);

  useEffect(() => {
    if (!isNavigating) return;

    const timeout = window.setTimeout(() => {
      setIsNavigating(false);
      setPendingHref(null);
      startedAtRef.current = null;
    }, FAILSAFE_MS);

    return () => window.clearTimeout(timeout);
  }, [isNavigating]);

  const value = useMemo(
    () => ({ isNavigating, pendingHref, beginNavigation }),
    [beginNavigation, isNavigating, pendingHref],
  );

  return (
    <RouteTransitionContext.Provider value={value}>
      {children}
      <RouteTransitionOverlay isVisible={isNavigating} />
    </RouteTransitionContext.Provider>
  );
}

export function useRouteTransition() {
  const context = useContext(RouteTransitionContext);
  if (!context) {
    throw new Error("useRouteTransition must be used within RouteTransitionProvider");
  }
  return context;
}

function RouteTransitionOverlay({ isVisible }: { isVisible: boolean }) {
  /* Thin top bar only — avoids stacking with route-level PageSkeleton (full overlay). */
  return (
    <div
      aria-hidden={!isVisible}
      className={cn(
        "pointer-events-none fixed inset-x-0 top-0 z-[80] transition-opacity duration-300",
        isVisible ? "opacity-100" : "opacity-0",
      )}
    >
      <div className="relative h-1 overflow-hidden bg-primary/10">
        <div className="route-loading-bar absolute inset-y-0 left-0 w-full" />
      </div>
    </div>
  );
}
