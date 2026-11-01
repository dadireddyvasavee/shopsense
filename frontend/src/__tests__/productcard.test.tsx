import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ProductCard } from "../components/ProductCard";

const p = { id: 1, sku: "DEMO-001", name: "Nimbus Air 14", brand: "Nimbus", description: "", price: 58990, specifications: {}, attributes: ["programming"],
  image_url: null, source: "demo", category: { id: 1, slug: "laptops", name: "Laptops" } };

test("product card shows price in INR and reasons", () => {
  render(<MemoryRouter><ProductCard p={p} reasons={["Within your budget"]} /></MemoryRouter>);
  expect(screen.getByText("Nimbus Air 14")).toBeInTheDocument();
  expect(screen.getByText(/58,990/)).toBeInTheDocument();
  expect(screen.getByText(/Within your budget/)).toBeInTheDocument();
});
