import React from 'react';

export function HeroTitle() {
  return (
    <div className="text-center relative">
      {/* Moon background */}
      <div 
        className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[400px] h-[400px] opacity-75 pointer-events-none"
        style={{
          backgroundImage: `url('https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/31955c23-347f-4a63-a346-730268693c3b/dc6vkzm-46373709-9365-48f5-a6e1-24044d6ae193.png?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcLzMxOTU1YzIzLTM0N2YtNGE2My1hMzQ2LTczMDI2ODY5M2MzYlwvZGM2dmt6bS00NjM3MzcwOS05MzY1LTQ4ZjUtYTZlMS0yNDA0NGQ2YWUxOTMucG5nIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.zodSbYNS-ydwLVbf-43CRNspP5UlAumeV47DpWhEqPs')`,
          backgroundSize: 'contain',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          filter: 'brightness(0.8) contrast(1.2)'
        }}
      />
      
      {/* Text content */}
      <div className="relative z-10">
        <h1 className="text-4xl md:text-5xl font-bold mb-6">
          Complex Simplicity Media
        </h1>
        <div className="text-xl md:text-2xl lg:text-3xl flex flex-col items-center space-y-3">
          <span className="text-white font-bold">
            Masters of the
          </span>
          <div className="relative">
            <span className="absolute inset-0 bg-gradient-to-r from-purple-500 via-blue-500 to-purple-500 blur-2xl opacity-30" 
                  style={{ clipPath: 'inset(0)' }} />
            <span className="relative inline-block bg-gradient-to-r from-white/30 to-white/20 text-white px-6 py-2 transform -skew-x-12 font-bold backdrop-blur-sm border border-white/10 shadow-2xl">
              Complexity
            </span>
          </div>
          <span className="text-white font-bold">
            of Simplicity
          </span>
        </div>
      </div>
    </div>
  );
}