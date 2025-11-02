import React from 'react';

interface HeaderProps {
  currentLocation?: string;
}

export default function Header({ currentLocation }: HeaderProps) {
  return (
    <header className="pt-5 pb-3 flex flex-col items-center border-b border-[#3a3a3a] bg-[#3a3a3a]">
      <h1 className="text-white text-lg font-bold">🍔 Ăn gì? 🍔</h1>
      <p className="text-[#bdbdbd] text-xs">AI Food reviewer</p>
      {currentLocation && (
        <p className="text-[#bdbdbd] text-xs">
          Bạn đang ở: {currentLocation}
        </p>
      )}
    </header>
  );
}