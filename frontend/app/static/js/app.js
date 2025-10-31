document.addEventListener('DOMContentLoaded', function() {
	const form = document.getElementById('facturaForm');
	const pdfViewer = document.getElementById('pdfViewer');
	const pdfFrame = document.getElementById('pdfFrame');
	const downloadBtn = document.getElementById('downloadBtn');

	if (!form) return;

	form.addEventListener('submit', async function(e) {
		e.preventDefault();

		const idInput = document.getElementById('id_factura');
		const idFactura = idInput ? idInput.value.trim() : '';
		if (!idFactura) {
			alert('Ingrese un número de factura');
			return;
		}

		const submitBtn = form.querySelector('button[type="submit"]');
		submitBtn.disabled = true;
		const oldText = submitBtn.textContent;
		submitBtn.textContent = 'Generando...';

		try {
			const resp = await fetch('/generar-pdf', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ id_factura: idFactura })
			});

			if (!resp.ok) {
				const txt = await resp.text();
				throw new Error(txt || 'Error al generar el PDF');
			}

			const blob = await resp.blob();
			const url = URL.createObjectURL(blob);

			// Mostrar en iframe y ajustar enlace de descarga
			pdfFrame.src = url;
			downloadBtn.href = url;
			downloadBtn.setAttribute('download', `factura_${idFactura}.pdf`);
			pdfViewer.classList.remove('hidden');

			// Liberar URL al descargar/recargar
			downloadBtn.addEventListener('click', () => setTimeout(() => URL.revokeObjectURL(url), 200));
		} catch (err) {
			console.error(err);
			alert('No se pudo generar el PDF. ' + (err.message || ''));
		} finally {
			submitBtn.disabled = false;
			submitBtn.textContent = oldText;
		}
	});
});

