import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";

import Home from "@/app/page";

describe("Landing page", () => {
  it("renders the hero heading", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { level: 1, name: /skate assistant/i }),
    ).toBeInTheDocument();
  });

  it("mounts the shadcn Button (verifies component pipeline)", () => {
    render(<Home />);
    expect(
      screen.getByRole("button", { name: /pipeline check/i }),
    ).toBeInTheDocument();
  });
});
