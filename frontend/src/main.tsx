import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import "./index.css"
import App from "./App.jsx"

console.log("main.tsx loaded")

const root = document.getElementById("root")
if (!root) {
  throw new Error("Root container missing in index.html")
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>
)