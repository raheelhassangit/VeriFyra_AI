import React from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { ShieldCheck, LayoutDashboard, FolderKanban, ScanSearch, Scale, LogOut, ExternalLink, Menu, X } from "lucide-react";
import { useState } from "react";
import { useAuth } from "../auth/AuthContext";

export default function Shell() {
  const { user, logout } = useAuth();
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const admin = user?.role === "ADMIN";
  const judge = user?.role === "JUDGE";
  const links = [
    { to: "/app", label: "Overview", icon: LayoutDashboard, end: true },
    ...(!judge ? [{ to: "/app/projects", label: "Projects", icon: FolderKanban }] : []),
    ...(!judge ? [{ to: "/app/audits", label: "AI audits", icon: ScanSearch }] : []),
    ...(judge ? [{ to: "/app/judging", label: "Judging desk", icon: Scale }] : []),
  ];
  const signOut = async () => { await logout(); navigate("/login"); };
  return <div className="app-shell">
    <aside className={`sidebar ${mobileOpen ? "sidebar-open" : ""}`}>
      <div className="brand"><div className="brand-mark"><ShieldCheck size={22}/></div><div><b>VeriFyra</b><small>TRUST INTELLIGENCE</small></div><button className="icon-btn mobile-close" onClick={() => setMobileOpen(false)}><X/></button></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav>{links.map(({to,label,icon:Icon,end}) => <NavLink key={to} to={to} end={end} onClick={() => setMobileOpen(false)} className={({isActive}) => `nav-link ${isActive ? "active" : ""}`}><Icon size={18}/><span>{label}</span></NavLink>)}</nav>
      <div className="sidebar-bottom"><div className="security-note"><span className="live-dot"/>AI services configured separately<br/><small>Protected API connection</small></div><a className="nav-link" href={`${import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000/api/v1"}/docs/`} target="_blank" rel="noreferrer"><ExternalLink size={17}/>API documentation</a></div>
    </aside>
    {mobileOpen && <button className="mobile-scrim" onClick={() => setMobileOpen(false)} aria-label="Close menu"/>}
    <main className="main-area"><header className="topbar"><button className="icon-btn mobile-menu" onClick={() => setMobileOpen(true)}><Menu/></button><div className="breadcrumb">Workspace <span>/</span> <b>{links.find(l => location.pathname === l.to)?.label || "Overview"}</b></div><div className="user-menu"><div className="avatar">{(user?.full_name || user?.email || "U").slice(0,1).toUpperCase()}</div><div className="user-info"><b>{user?.full_name || user?.email}</b><small>{user?.role || "USER"}</small></div><button className="icon-btn" title="Sign out" onClick={signOut}><LogOut size={17}/></button></div></header><div className="page-content"><Outlet/></div></main>
  </div>;
}