import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

export function Breadcrumbs() {
  const { currentPath, setCurrentPath } = useCloudStore();

  return (
    <div className="cloud-breadcrumbs">
      {currentPath.map((segment, index) => (
        <button
          key={segment}
          className="cloud-breadcrumbs__item"
          onClick={() => setCurrentPath(currentPath.slice(0, index + 1))}
        >
          {segment}
        </button>
      ))}
    </div>
  );
}
