/**
 * PWA Icon Generator Script
 * Run from webapp folder: node ../scripts/generate-icons.js
 * 
 * Requires: npm install sharp
 */

const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const iconDir = path.join(process.cwd(), 'public/icons');

// Ensure icons directory exists
if (!fs.existsSync(iconDir)) {
  fs.mkdirSync(iconDir, { recursive: true });
}

// Create a simple icon using sharp
async function generateIcons() {
  // Create base icon as SVG buffer
  const svgIcon = `
    <svg width="512" height="512" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#1a1a2e"/>
          <stop offset="50%" style="stop-color:#16213e"/>
          <stop offset="100%" style="stop-color:#0f3460"/>
        </linearGradient>
        <linearGradient id="accent" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" style="stop-color:#1DB954"/>
          <stop offset="100%" style="stop-color:#1ed760"/>
        </linearGradient>
      </defs>
      
      <!-- Background -->
      <rect width="512" height="512" rx="96" fill="url(#bg)"/>
      
      <!-- Vinyl disc -->
      <circle cx="256" cy="256" r="160" fill="#1a1a1a" stroke="#333" stroke-width="2"/>
      <circle cx="256" cy="256" r="140" fill="none" stroke="#2a2a2a" stroke-width="1"/>
      <circle cx="256" cy="256" r="120" fill="none" stroke="#2a2a2a" stroke-width="1"/>
      <circle cx="256" cy="256" r="100" fill="none" stroke="#2a2a2a" stroke-width="1"/>
      <circle cx="256" cy="256" r="80" fill="none" stroke="#2a2a2a" stroke-width="1"/>
      
      <!-- Center label -->
      <circle cx="256" cy="256" r="50" fill="url(#accent)"/>
      <circle cx="256" cy="256" r="12" fill="#121212"/>
      
      <!-- Play button overlay -->
      <path d="M240 200 L240 312 L320 256 Z" fill="white" opacity="0.9"/>
      
      <!-- TG text -->
      <text x="256" y="440" text-anchor="middle" font-family="Arial, sans-serif" font-size="48" font-weight="bold" fill="white">TG</text>
    </svg>
  `;

  const svgBuffer = Buffer.from(svgIcon);

  for (const size of sizes) {
    const outputPath = path.join(iconDir, `icon-${size}x${size}.png`);
    
    await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toFile(outputPath);
    
    console.log(`Generated: icon-${size}x${size}.png`);
  }

  console.log('All icons generated successfully!');
}

generateIcons().catch(console.error);
