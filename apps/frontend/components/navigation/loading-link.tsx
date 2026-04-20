"use client";

import Link, { type LinkProps } from "next/link";
import { forwardRef, type ComponentPropsWithoutRef, type MouseEvent } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { useRouteTransition } from "@/components/layout/route-transition-provider";

type LoadingLinkProps = LinkProps &
  Omit<ComponentPropsWithoutRef<typeof Link>, keyof LinkProps> & {
    skipLoadingTransition?: boolean;
  };

export const LoadingLink = forwardRef<HTMLAnchorElement, LoadingLinkProps>(
  function LoadingLink(
    { href, onClick, skipLoadingTransition = false, ...props },
    ref,
  ) {
    const pathname = usePathname();
    const searchParams = useSearchParams();
    const { beginNavigation } = useRouteTransition();
    const currentHref = `${pathname}${searchParams.toString() ? `?${searchParams.toString()}` : ""}`;

    const handleClick = (event: MouseEvent<HTMLAnchorElement>) => {
      onClick?.(event);
      if (event.defaultPrevented || skipLoadingTransition) return;
      if (isModifiedEvent(event) || props.target === "_blank") return;

      const nextHref = typeof href === "string" ? href : href.pathname ?? currentHref;
      if (typeof nextHref === "string" && normalizeHref(nextHref) === normalizeHref(currentHref)) {
        return;
      }

      beginNavigation(typeof nextHref === "string" ? nextHref : null);
    };

    return <Link ref={ref} href={href} onClick={handleClick} {...props} />;
  },
);

function isModifiedEvent(event: MouseEvent<HTMLAnchorElement>) {
  return event.metaKey || event.ctrlKey || event.shiftKey || event.altKey || event.button !== 0;
}

function normalizeHref(value: string) {
  return value.replace(/\/+$/, "") || "/";
}
