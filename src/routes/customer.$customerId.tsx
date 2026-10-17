import { createFileRoute, redirect } from "@tanstack/react-router";

// Legacy URL — customer detail now lives under /customers.
export const Route = createFileRoute("/customer/$customerId")({
  beforeLoad: ({ params }) => {
    throw redirect({ to: "/customers/$customerId", params: { customerId: params.customerId }, statusCode: 301 });
  },
});
