import { clerkMiddleware, createRouteMatcher } from "@clerk/nextjs/server";
import { type NextMiddleware, type NextRequest, type NextFetchEvent, NextResponse } from "next/server";

const isPublicRoute = createRouteMatcher([
  "/",
  "/login(.*)",
  "/register(.*)",
  "/api(.*)",
  "/monitoring(.*)",
]);

let clerkHandler: NextMiddleware | null = null;

function getClerkHandler(): NextMiddleware {
  if (!clerkHandler) {
    clerkHandler = clerkMiddleware((auth, req) => {
      if (!isPublicRoute(req)) {
        auth().protect();
      }
    });
  }
  return clerkHandler;
}

export default function middleware(req: NextRequest, event: NextFetchEvent) {
  if (!process.env.NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY) {
    return NextResponse.next();
  }

  try {
    const handler = getClerkHandler();
    if (handler) {
      return handler(req, event);
    }
  } catch (error) {
    console.warn("Clerk middleware execution fallback:", error);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    // Skip Next.js internals and static files
    "/((?!_next|[^?]*\\.(?:html?|css|js(?!on)|jpe?g|webp|png|gif|svg|ttf|woff2?|ico|csv|docx?|xlsx?|zip|webmanifest)).*)",
    // Always run for API routes
    "/(api|trpc)(.*)",
  ],
};
