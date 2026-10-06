import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
// @ts-ignore -- Vite handles this stylesheet import.
import "./index.css";
import App from "./App";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
