import React, { useState } from 'react';
import { PdfPreview } from './PdfPreview';

export const App: React.FC = () => {
  const [message, setMessage] = useState('');

  async function ping() {
    try {
      const res = await fetch('http://127.0.0.1:5000/ping');
      const data = await res.json();
      setMessage(data.message || JSON.stringify(data));
    } catch (e) {
      setMessage(String(e));
    }
  }

  return (
    <div>
      <button onClick={ping}>Ping</button>
      <p>{message}</p>
      <PdfPreview url="/sample.pdf" />
    </div>
  );
};
