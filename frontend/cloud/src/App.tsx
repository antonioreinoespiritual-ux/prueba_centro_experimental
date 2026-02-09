import React from 'react';
import { Topbar } from './components/Topbar';
import { Sidebar } from './components/Sidebar';
import { Breadcrumbs } from './components/Breadcrumbs';
import { FileList } from './components/FileList';
import { FileGrid } from './components/FileGrid';
import { DetailsPanel } from './components/DetailsPanel';
import { useCloudStore } from './store/useCloudStore';
import { useEffect } from 'react';

export default function App() {
  const { viewMode, loadLibraries, createFolder, uploadFile, toast, clearToast } = useCloudStore();

  useEffect(() => {
    loadLibraries();
  }, [loadLibraries]);

  useEffect(() => {
    if (!toast) return undefined;
    const timeout = window.setTimeout(() => clearToast(), 3000);
    return () => window.clearTimeout(timeout);
  }, [toast, clearToast]);

  const handleCreateFolder = async () => {
    const name = window.prompt('Nombre de la carpeta');
    if (!name) return;
    await createFolder(name);
  };

  const handleUploadFile = async (file: File) => {
    await uploadFile(file);
  };

  return (
    <div className="cloud-app">
      <Topbar onCreateFolder={handleCreateFolder} onUploadFile={handleUploadFile} />
      <div className="cloud-layout">
        <Sidebar />
        <main className="cloud-main">
          <div className="cloud-main__header">
            <div>
              <h1>Cloud Drive</h1>
              <p>Bibliotecas por hipótesis y records.</p>
              <Breadcrumbs />
            </div>
          </div>
          {viewMode === 'list' ? <FileList /> : <FileGrid />}
        </main>
        <DetailsPanel />
      </div>
      {toast && <div className="cloud-toast">{toast}</div>}
    </div>
  );
}
