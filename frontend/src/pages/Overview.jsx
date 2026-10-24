import React from "react";
import { useEffect, useState } from "react";
import { ArrowUpRight, FolderKanban, ScanSearch, CircleCheck, Clock3, Plus, ShieldCheck, Activity, Sparkles } from "lucide-react";
import { Link } from "react-router-dom";
import api, { getErrorMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";

const statusTone = (s="") => ({COMPLETED:"success",SUCCEEDED:"success",FAILED:"danger",RUNNING:"info",QUEUED:"warning",PENDING:"warning",CANCELLED:"neutral"}[s.toUpperCase()] || "neutral");
export default function Overview() {
  const { user } = useAuth();
  const [projects, setProjects] = useState([]);
  const [audits, setAudits] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    Promise.all([api.get("/projects/"), api.get("/audits/")]).then(([p,a]) => {
      setProjects(p.data.results || p.data); setAudits(a.data.results || a.data);
    }).catch(e => setError(getErrorMessage(e))).finally(() => setLoading(false));
  }, []);
  const done = audits.filter(a => ["COMPLETED","SUCCEEDED"].includes((a.status || "").toUpperCase())).length;
  return <><div className="page-heading"><div><div className="eyebrow">YOUR COMMAND CENTER</div><h1>Good to see you, {(user?.full_name || "there").split(" ")[0]}.</h1><p>Here's the latest from your verification workspace.</p></div><Link className="btn btn-primary" to="/app/projects"><Plus size={17}/> Add project</Link></div>
    {error && <div className="alert error">{error} <span>Check your backend URL and API availability.</span></div>}
    <div className="welcome-banner"><div className="banner-orb"><ShieldCheck size={28}/></div><div><span className="banner-kicker">VERIFICATION WORKSPACE <span className="banner-pill">● ACTIVE</span></span><h2>Evidence first. Decisions with confidence.</h2><p>Connect a repository, run a multi-agent audit, and review the evidence behind every finding.</p></div><div className="banner-decoration">V<span>F</span></div></div>
    <div className="section-head"><div><h2>Workspace overview</h2><p>Live data from your VeriFyra API</p></div><span className="sync-label"><span className="live-dot"/> API connected when available</span></div>
    <div className="stat-grid"><Stat icon={FolderKanban} label="Your projects" value={loading ? "—" : projects.length} note="Registered repositories" tone="violet"/><Stat icon={ScanSearch} label="Audit runs" value={loading ? "—" : audits.length} note="Total verification runs" tone="blue"/><Stat icon={CircleCheck} label="Completed audits" value={loading ? "—" : done} note="Successfully finished" tone="green"/><Stat icon={Activity} label="In progress" value={loading ? "—" : audits.filter(a => ["RUNNING","QUEUED","PENDING"].includes((a.status||"").toUpperCase())).length} note="Active or queued" tone="amber"/></div>
    <div className="content-grid"><section className="panel"><div className="panel-head"><div><h3>Recent projects</h3><p>Repositories in your workspace</p></div><Link to="/app/projects" className="text-link">View all <ArrowUpRight size={15}/></Link></div>{loading ? <div className="empty-state">Loading projects…</div> : projects.length ? <div className="table-list">{projects.slice(0,5).map(p=><div className="list-row" key={p.id}><div className="row-icon violet"><FolderKanban size={18}/></div><div className="row-main"><b>{p.name}</b><small>{p.github_url}</small></div><span className={`status-pill ${p.visibility === "PUBLISHED" ? "success" : "neutral"}`}>{p.visibility || "PRIVATE"}</span></div>)}</div> : <Empty icon={FolderKanban} title="No projects yet" text="Register a GitHub repository to start your first audit." action={<Link className="btn btn-secondary btn-sm" to="/app/projects"><Plus size={15}/> Add a project</Link>}/>}</section>
    <section className="panel"><div className="panel-head"><div><h3>Recent audits</h3><p>Latest agent execution runs</p></div><Link to="/app/audits" className="text-link">View all <ArrowUpRight size={15}/></Link></div>{loading ? <div className="empty-state">Loading audits…</div> : audits.length ? <div className="table-list">{audits.slice(0,5).map(a=><div className="list-row" key={a.id}><div className="row-icon blue"><ScanSearch size={18}/></div><div className="row-main"><b>Audit #{String(a.id).slice(0,8)}</b><small>{a.current_stage || "Awaiting stage"} · {a.progress_percentage ?? 0}%</small></div><span className={`status-pill ${statusTone(a.status)}`}>{a.status}</span></div>)}</div> : <Empty icon={ScanSearch} title="No audits run" text="Your audit history and agent findings will appear here." action={<Link className="text-link" to="/app/projects">Go to projects <ArrowUpRight size={15}/></Link>}/>}</section></div>
    <div className="bottom-tip"><div className="tip-icon"><Sparkles size={19}/></div><div><b>Make every verdict explainable</b><p>Review the agent outputs and evidence for each audit before acting on its overall score.</p></div><Link to="/app/audits" className="text-link">Explore audits <ArrowUpRight size={15}/></Link></div>
  </>;
}
function Stat({icon:Icon,label,value,note,tone}){return <div className="stat-card"><div className={`stat-icon ${tone}`}><Icon size={19}/></div><div className="stat-label">{label}</div><div className="stat-value">{value}</div><div className="stat-note">{note}</div></div>}
function Empty({icon:Icon,title,text,action}){return <div className="empty-state"><div className="empty-icon"><Icon size={22}/></div><b>{title}</b><p>{text}</p>{action}</div>}