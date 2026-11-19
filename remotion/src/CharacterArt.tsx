import React from "react";
import { AbsoluteFill } from "remotion";

// Original placeholder art for the channel character "Uncle Ji" (see characters/uncle_ji.md):
// round glasses, grey moustache, white kurta, shocked-happy face. Rendered once to characters/uncle_ji.png.
// Replace that PNG with professional art any time; nothing else changes.
export const UncleJi: React.FC = () => (
  <AbsoluteFill>
    <svg viewBox="0 0 900 1300" width="100%" height="100%">
      {/* kurta */}
      <path d="M150 1300 C150 980 260 860 450 860 C640 860 750 980 750 1300 Z" fill="#fbfbf7" stroke="#1d1d1d" strokeWidth="14" />
      <path d="M450 880 L450 1120" stroke="#1d1d1d" strokeWidth="10" />
      <circle cx="450" cy="960" r="10" fill="#1d1d1d" /><circle cx="450" cy="1030" r="10" fill="#1d1d1d" />
      {/* neck */}
      <rect x="395" y="770" width="110" height="110" rx="30" fill="#d79a6b" stroke="#1d1d1d" strokeWidth="12" />
      {/* ears */}
      <ellipse cx="205" cy="520" rx="55" ry="80" fill="#d79a6b" stroke="#1d1d1d" strokeWidth="12" />
      <ellipse cx="695" cy="520" rx="55" ry="80" fill="#d79a6b" stroke="#1d1d1d" strokeWidth="12" />
      {/* head */}
      <ellipse cx="450" cy="470" rx="250" ry="320" fill="#e2a876" stroke="#1d1d1d" strokeWidth="14" />
      {/* bald shine + grey side hair */}
      <ellipse cx="380" cy="230" rx="70" ry="30" fill="#f3c9a0" />
      <path d="M215 430 C200 330 230 280 270 260 C250 330 255 380 262 440 Z" fill="#c9c9c9" stroke="#1d1d1d" strokeWidth="10" />
      <path d="M685 430 C700 330 670 280 630 260 C650 330 645 380 638 440 Z" fill="#c9c9c9" stroke="#1d1d1d" strokeWidth="10" />
      {/* raised eyebrows (shock) */}
      <path d="M290 345 Q350 300 410 340" stroke="#8a8a8a" strokeWidth="22" fill="none" strokeLinecap="round" />
      <path d="M490 340 Q550 300 610 345" stroke="#8a8a8a" strokeWidth="22" fill="none" strokeLinecap="round" />
      {/* round glasses */}
      <circle cx="350" cy="440" r="78" fill="#ffffff" fillOpacity="0.55" stroke="#1d1d1d" strokeWidth="14" />
      <circle cx="550" cy="440" r="78" fill="#ffffff" fillOpacity="0.55" stroke="#1d1d1d" strokeWidth="14" />
      <path d="M428 435 Q450 415 472 435" stroke="#1d1d1d" strokeWidth="12" fill="none" />
      {/* wide eyes */}
      <circle cx="350" cy="445" r="30" fill="#1d1d1d" /><circle cx="550" cy="445" r="30" fill="#1d1d1d" />
      <circle cx="360" cy="433" r="10" fill="#ffffff" /><circle cx="560" cy="433" r="10" fill="#ffffff" />
      {/* nose */}
      <path d="M450 480 Q485 560 450 585 Q430 590 420 575" stroke="#1d1d1d" strokeWidth="10" fill="#d48f5e" />
      {/* big grey moustache */}
      <path d="M300 640 Q330 590 450 610 Q570 590 600 640 Q560 668 520 650 Q480 640 450 655 Q420 640 380 650 Q340 668 300 640 Z"
            fill="#9e9e9e" stroke="#1d1d1d" strokeWidth="10" />
      {/* open "arey baap re!" mouth */}
      <ellipse cx="450" cy="705" rx="62" ry="48" fill="#7a1f1f" stroke="#1d1d1d" strokeWidth="10" />
      <ellipse cx="450" cy="725" rx="34" ry="18" fill="#e5675f" />
      {/* cheeks */}
      <circle cx="285" cy="590" r="34" fill="#ef8d7a" fillOpacity="0.5" />
      <circle cx="615" cy="590" r="34" fill="#ef8d7a" fillOpacity="0.5" />
    </svg>
  </AbsoluteFill>
);
