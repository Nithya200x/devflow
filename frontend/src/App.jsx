import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Login, Sidebar, Dashboard, Projects, Deployments, Clusters, Incidents } from './components';

const AppLayout = ({ children }) => {
  const token = localStorage.getItem('token');
  if (!token) return <Navigate to="/login" replace />;

  return (
    <div className="app-container">
      <Sidebar />
      <div className="main-content">
        {children}
      </div>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/" element={<AppLayout><Dashboard /></AppLayout>} />
        <Route path="/projects" element={<AppLayout><Projects /></AppLayout>} />
        <Route path="/deployments" element={<AppLayout><Deployments /></AppLayout>} />
        <Route path="/clusters" element={<AppLayout><Clusters /></AppLayout>} />
        <Route path="/incidents" element={<AppLayout><Incidents /></AppLayout>} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
