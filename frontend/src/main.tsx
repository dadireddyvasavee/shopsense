import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";
import Shell from "./components/Shell";
import { RequireAuth } from "./components/ui";
import { AuthProvider } from "./lib/auth";
import Assistant from "./pages/Assistant";
import { Login, Register } from "./pages/AuthPages";
import Compare from "./pages/Compare";
import Discover from "./pages/Discover";
import Home from "./pages/Home";
import Landing from "./pages/Landing";
import ProductDetail from "./pages/ProductDetail";
import Profile from "./pages/Profile";
import Saved from "./pages/Saved";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login brand="ShopSense" />} />
          <Route path="/register" element={<Register brand="ShopSense" />} />
          <Route element={<RequireAuth />}>
            <Route path="/app" element={<Shell />}>
              <Route index element={<Home />} />
              <Route path="discover" element={<Discover />} />
              <Route path="products/:id" element={<ProductDetail />} />
              <Route path="assistant" element={<Assistant />} />
              <Route path="compare" element={<Compare />} />
              <Route path="saved" element={<Saved />} />
              <Route path="profile" element={<Profile />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
);
