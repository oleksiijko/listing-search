import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { ErrorBoundary } from "react-error-boundary";
import { App } from "./app";
import "./styles.css";

const container = document.getElementById("root");
if (!container) {
  throw new Error("The application container is missing.");
}

createRoot(container).render(
  <StrictMode>
    <ErrorBoundary
      fallback={
        <main role="alert" className="mx-auto max-w-2xl p-8">
          <h1 className="text-xl font-semibold">Listing Search could not start</h1>
          <p className="mt-2">Reload the page to try again.</p>
        </main>
      }
    >
      <App />
    </ErrorBoundary>
  </StrictMode>,
);
