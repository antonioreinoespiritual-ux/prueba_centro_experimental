import React, { useEffect, useRef } from 'react';
import { Topbar } from './components/Topbar';
import { Sidebar } from './components/Sidebar';
import { Breadcrumbs } from './components/Breadcrumbs';
import { FileList } from './components/FileList';
import { FileGrid } from './components/FileGrid';
import { DetailsPanel } from './components/DetailsPanel';
import { useCloudStore } from './store/useCloudStore';
import { fetchExperimentDrivePath, fetchRecordDrivePath } from './api/cloud';

export default function App() {
  const { viewMode, loadLibraries, createFolder, uploadFile, toast, clearToast, libraries, openSystemRelPath } =
    useCloudStore();
  const deepLinkHandled = useRef(false);

  useEffect(() => {
    loadLibraries();
  }, [loadLibraries]);

  useEffect(() => {
    if (deepLinkHandled.current || libraries.length === 0) return;
    const params = new URLSearchParams(window.location.search);
    const type = params.get('type');
    const idParam = params.get('id');
    if (!type || !idParam) return;
    const id = Number(idParam);
    if (!Number.isFinite(id)) return;
    deepLinkHandled.current = true;
    (async () => {
      try {
        const relPath =
          type === 'experiment'
            ? await fetchExperimentDrivePath(id)
            : type === 'record'
              ? await fetchRecordDrivePath(id)
              : null;
        if (relPath) {
          await openSystemRelPath(relPath);
        }
      } catch (error) {
        console.error('Error resolving drive path', error);
      }
    })();
  }, [libraries, openSystemRelPath]);

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
              <p>Bibliotecas organizadas por proyectos, hipótesis y records.</p>
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
