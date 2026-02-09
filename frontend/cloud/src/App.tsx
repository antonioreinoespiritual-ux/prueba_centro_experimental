import React from 'react';
import { Topbar } from './components/Topbar';
import { Sidebar } from './components/Sidebar';
import { Breadcrumbs } from './components/Breadcrumbs';
import { FileList } from './components/FileList';
import { FileGrid } from './components/FileGrid';
import { DetailsPanel } from './components/DetailsPanel';
import { useCloudStore } from './store/useCloudStore';

export default function App() {
  const { viewMode } = useCloudStore();

  return (
    <div className="cloud-app">
      <Topbar />
      <div className="cloud-layout">
        <Sidebar />
        <main className="cloud-main">
          <div className="cloud-main__header">
            <div>
              <h1>Cloud Drive</h1>
              <p>Bibliotecas por hipótesis y records.</p>
              <Breadcrumbs />
            </div>
            <div className="cloud-main__actions">
              <button className="cloud-btn">Compartir</button>
              <button className="cloud-btn">Mover</button>
            </div>
          </div>
          {viewMode === 'list' ? <FileList /> : <FileGrid />}
        </main>
        <DetailsPanel />
      </div>
    </div>
  );
}
