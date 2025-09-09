import React from 'react';
import { getDocument, GlobalWorkerOptions } from 'pdfjs-dist';
import workerSrc from 'pdfjs-dist/build/pdf.worker.min.js?url';

GlobalWorkerOptions.workerSrc = workerSrc;


interface Props {
  url: string;
}

export const PdfPreview: React.FC<Props> = ({ url }) => {
  const canvasRef = React.useRef<HTMLCanvasElement | null>(null);

  React.useEffect(() => {
    let cancelled = false;
    (async () => {
      const pdf = await getDocument(url).promise;
      const page = await pdf.getPage(1);
      const viewport = page.getViewport({ scale: 1.0 });
      const canvas = canvasRef.current;
      if (!canvas || cancelled) return;
      const context = canvas.getContext('2d');
      if (!context) return;
      canvas.height = viewport.height;
      canvas.width = viewport.width;
      await page.render({ canvasContext: context, viewport }).promise;
    })();
    return () => {
      cancelled = true;
    };
  }, [url]);

  return <canvas ref={canvasRef} style={{ width: '100%' }} />;
};
