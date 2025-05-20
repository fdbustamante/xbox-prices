import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App' // Updated import path
// Si tu CSS principal no está importado en App.jsx, impórtalo aquí
// import './index.css' // o './style.css'

const rootElement = document.getElementById('root');

if (rootElement) {
  ReactDOM.createRoot(rootElement).render(
    <React.StrictMode>
      <App />
    </React.StrictMode>,
  );
} else {
  console.error("Failed to find the root element");
}
