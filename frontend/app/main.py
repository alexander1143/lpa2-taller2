from flask import Flask, render_template, request, send_file, abort
import requests
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import mm
from io import BytesIO
import os

app = Flask(__name__)
BACKEND_URL = os.getenv('BACKEND_URL', 'http://localhost:8001')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generar-pdf', methods=['POST'])
def generar_pdf():
    try:
        # Obtener el ID de factura del formulario o JSON
        if request.is_json:
            id_factura = request.json.get('id_factura')
        else:
            id_factura = request.form.get('id_factura')

        if not id_factura:
            abort(400, description="ID de factura requerido")

        # Consultar al backend
        response = requests.get(f"{BACKEND_URL}/facturas/v1/{id_factura}")
        if response.status_code != 200:
            abort(response.status_code, description="Error al obtener datos de la factura")
        
        datos_factura = response.json()

        # Normalizar el nombre del campo de items según el backend (usa 'detalle')
        items = datos_factura.get('detalle') or datos_factura.get('items') or []

        # Crear PDF en memoria
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=20*mm, leftMargin=20*mm, topMargin=20*mm, bottomMargin=20*mm)
        story = []
        styles = getSampleStyleSheet()

        # Encabezado
        numero = datos_factura.get('numero_factura', id_factura)
        story.append(Paragraph(f"Factura #{numero}", styles['Heading1']))
        story.append(Spacer(1, 12))

        # Datos de la empresa
        story.append(Paragraph("Datos de la Empresa:", styles['Heading2']))
        empresa = datos_factura.get('empresa', {})
        empresa_data = [
            ["Nombre:", empresa.get('nombre', '')],
            ["Dirección:", empresa.get('direccion', '')],
            ["Teléfono:", empresa.get('telefono', '')],
            ["Email:", empresa.get('email', '')]
        ]
        t = Table(empresa_data, colWidths=[100, 400])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Datos del cliente
        story.append(Paragraph("Datos del Cliente:", styles['Heading2']))
        cliente = datos_factura.get('cliente', {})
        cliente_data = [
            ["Nombre:", cliente.get('nombre', '')],
            ["Dirección:", cliente.get('direccion', '')],
            ["Teléfono:", cliente.get('telefono', '')],
            ["Email:", cliente.get('email', '')]
        ]
        t = Table(cliente_data, colWidths=[100, 400])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (-1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Detalles de la factura
        story.append(Paragraph("Detalles de la Factura:", styles['Heading2']))
        items_header = [["Ítem", "Cantidad", "Precio Unitario", "Total"]]
        items_data = []
        for item in items:
            desc = item.get('descripcion', '')
            cantidad = item.get('cantidad', 0)
            pu = item.get('precio_unitario', item.get('precio', 0.0))
            total_item = round(cantidad * pu, 2)
            items_data.append([desc, str(cantidad), f"${pu:.2f}", f"${total_item:.2f}"])

        # Totales (si vienen del backend, úsalos)
        subtotal = datos_factura.get('subtotal')
        impuesto = datos_factura.get('impuesto')
        total = datos_factura.get('total')
        if subtotal is None:
            subtotal = sum((item.get('precio_unitario', 0.0) * item.get('cantidad', 0)) for item in items)
            impuesto = round(subtotal * 0.21, 2)
            total = round(subtotal + impuesto, 2)

        items_data.append(["Subtotal", "", "", f"${subtotal:.2f}"])
        items_data.append(["Impuesto (21%)", "", "", f"${impuesto:.2f}"])
        items_data.append(["TOTAL", "", "", f"${total:.2f}"])

        t = Table(items_header + items_data, colWidths=[200, 100, 100, 100])
        t.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 10),
            ('GRID', (0,0), (-2,-4), 0.5, colors.grey),
            ('LINEBELOW', (0,-1), (-1,-1), 1.5, colors.black),
            ('FONTNAME', (0,-3), (-1,-1), 'Helvetica-Bold'),
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ]))
        story.append(t)

        # Generar PDF
        doc.build(story)
        buffer.seek(0)

        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=False,
            download_name=f'factura_{numero}.pdf'
        )
    except requests.exceptions.ConnectionError:
        abort(503, description="Error de conexión con el servidor")
    except Exception as e:
        abort(500, description=str(e))

if __name__ == '__main__':
    # Puerto por defecto para el frontend: 5001
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)), debug=True)

