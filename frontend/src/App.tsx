import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./pages/Auth/Login";
import Register from "./pages/Auth/Register";
import Home from "./pages/Home/Home";
import Profile from "./pages/Profile/Profile";
import RecipeDetail from "./pages/Recipe/RecipeDetail";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/home" element={<Home />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/recipes/:slug" element={<RecipeDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
