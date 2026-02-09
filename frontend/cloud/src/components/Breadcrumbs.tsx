import React from 'react';
import { useCloudStore } from '../store/useCloudStore';

export function Breadcrumbs() {
  const { currentPath, goToBreadcrumb } = useCloudStore();

  return (
    <div className="cloud-breadcrumbs">
      {currentPath.map((segment, index) => (
        <button
          key={`${segment.name}-${index}`}
          className="cloud-breadcrumbs__item"
          onClick={() => goToBreadcrumb(index)}
        >
          {segment.name}
        </button>
      ))}
    </div>
  );
}
