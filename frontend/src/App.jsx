import React from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import Landing from "./pages/Landing";
import { useAuth } from "./auth/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Shell from "./components/Shell";
import Auth from "./pages/Auth";
import Overview from "./pages/Overview";
import Projects from "./pages/Projects";
import Audits from "./pages/Audits";
import Judging from "./pages/Judging";

function HomeRoute() {
 const { user, loading } = useAuth();
 if (loading) return <div className="loading-screen"><span className="spinner"/>Loading VeriFyra…</div>;
 return <Navigate to={user ? "/app" : "/login"} replace/>;
}
function DashboardRoute() {
 const { user } = useAuth();
 if (user?.role === "JUDGE") return <Navigate to="/app/judging" replace/>;
 return <Overview/>;
}
export default function App() {
 return <Routes>
  <Route path="/" element={<Landing/>}/>
  <Route path="/login" element={<Auth mode="login"/>}/>
  <Route path="/register" element={<Auth mode="register"/>}/>
  <Route element={<ProtectedRoute/>}><Route path="/app" element={<Shell/>}>
   <Route index element={<DashboardRoute/>}/>
   <Route element={<ProtectedRoute roles={["PARTICIPANT", "ADMIN"]}/> }>
    <Route path="projects" element={<Projects/>}/>
    <Route path="audits" element={<Audits/>}/>
   </Route>
   <Route element={<ProtectedRoute roles={["JUDGE"]}/>}>
    <Route path="judging" element={<Judging/>}/>
   </Route>
  </Route></Route>
  <Route path="*" element={<HomeRoute/>}/>
 </Routes>;
}