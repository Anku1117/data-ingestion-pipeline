import React from "react";
import { BrowserRouter, Routes, Route, NavLink } from "react-router-dom";
import Overview from "./pages/Overview";
import Events from "./pages/Events";
import Threats from "./pages/Threats";
import AgentRuns from "./pages/AgentRuns";
import Trajectory from "./pages/Trajectory";
import Evaluations from "./pages/Evaluations";
import PipelineHealth from "./pages/PipelineHealth";
import DLQ from "./pages/DLQ";

function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="sidebar">
          <div className="logo">
            <h1>DIP</h1>
            <p>Data Ingestion Platform</p>
          </div>
          <ul>
            <li><NavLink to="/" end>Overview</NavLink></li>
            <li><NavLink to="/events">Events</NavLink></li>
            <li><NavLink to="/threats">Threats</NavLink></li>
            <li><NavLink to="/agents">Agent Runs</NavLink></li>
            <li><NavLink to="/trajectory">Trajectory</NavLink></li>
            <li><NavLink to="/evaluations">Evaluations</NavLink></li>
            <li><NavLink to="/pipeline">Pipeline Health</NavLink></li>
            <li><NavLink to="/dlq">DLQ</NavLink></li>
          </ul>
        </nav>
        <main className="content">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/events" element={<Events />} />
            <Route path="/threats" element={<Threats />} />
            <Route path="/agents" element={<AgentRuns />} />
            <Route path="/trajectory" element={<Trajectory />} />
            <Route path="/evaluations" element={<Evaluations />} />
            <Route path="/pipeline" element={<PipelineHealth />} />
            <Route path="/dlq" element={<DLQ />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
