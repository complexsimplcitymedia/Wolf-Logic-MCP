import React from 'react';

export function VideoOverlay() {
  return (
    <>
      <div className="absolute inset-0 bg-gradient-to-b from-black/80 to-black/40 z-10" />
      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/60 z-10" />
      <div className="absolute inset-0 bg-gradient-to-r from-black/40 via-transparent to-black/40 z-10" />
    </>
  );
}