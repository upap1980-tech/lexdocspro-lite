"""
Dashboard Report Service
Genera reportes PDF profesionales basados en las estadísticas del dashboard
"""

import os
import tempfile
from datetime import datetime
from typing import Dict, List, Optional
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import matplotlib
matplotlib.use('Agg')  # Usar backend no interactivo
import matplotlib.pyplot as plt
import io
import base64

class DashboardReportService:
    """Servicio para generar reportes PDF del Dashboard"""
    
    def __init__(self, logo_path: Optional[str] = None):
        self.styles = getSampleStyleSheet()
        self.logo_path = logo_path
        self._setup_custom_styles()
        
    def _setup_custom_styles(self):
        """Configurar estilos personalizados para el reporte"""
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.hexColor('#1f2937'),
            alignment=TA_LEFT,
            spaceAfter=20
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=16,
            textColor=colors.hexColor('#3b82f6'),
            alignment=TA_LEFT,
            spaceBefore=15,
            spaceAfter=10
        ))
        
        self.styles.add(ParagraphStyle(
            name='KPILabel',
            fontSize=10,
            textColor=colors.hexColor('#6b7280'),
            alignment=TA_CENTER
        ))
        
        self.styles.add(ParagraphStyle(
            name='KPIValue',
            fontSize=20,
            fontName='Helvetica-Bold',
            textColor=colors.hexColor('#111827'),
            alignment=TA_CENTER
        ))

    def generate_report(self, stats: Dict, user_name: str = "Admin") -> str:
        """
        Generar reporte PDF y retornar la ruta al archivo temporal
        """
        fd, path = tempfile.mkstemp(suffix='.pdf')
        os.close(fd)
        
        doc = SimpleDocTemplate(
            path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        elements = []
        
        # 1. Cabecera y Título
        elements.append(Paragraph("LexDocsPro LITE", self.styles['ReportTitle']))
        elements.append(Paragraph(f"Reporte de Estadísticas del Sistema", self.styles['SectionHeader']))
        
        meta_info = f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} por {user_name}"
        elements.append(Paragraph(meta_info, self.styles['Normal']))
        elements.append(Spacer(1, 1*cm))
        
        # 2. Resumen de KPIs (Tabla)
        kpi_data = [
            [Paragraph("Hoy", self.styles['KPILabel']), 
             Paragraph("Semana", self.styles['KPILabel']), 
             Paragraph("Mes", self.styles['KPILabel']), 
             Paragraph("Total", self.styles['KPILabel'])],
            [Paragraph(str(stats.get('today', 0)), self.styles['KPIValue']),
             Paragraph(str(stats.get('week', 0)), self.styles['KPIValue']),
             Paragraph(str(stats.get('month', 0)), self.styles['KPIValue']),
             Paragraph(str(stats.get('total', 0)), self.styles['KPIValue'])]
        ]
        
        kpi_table = Table(kpi_data, colWidths=[4*cm]*4)
        kpi_table.setStyle(TableStyle([
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.hexColor('#e5e7eb')),
            ('BACKGROUND', (0,0), (-1,0), colors.hexColor('#f9fafb')),
            ('BOTTOMPADDING', (0,0), (-1,-1), 10),
            ('TOPPADDING', (0,0), (-1,-1), 10),
        ]))
        
        elements.append(kpi_table)
        elements.append(Spacer(1, 1*cm))
        
        # 3. Gráfica de Tendencia
        if stats.get('trend_data'):
            elements.append(Paragraph("Tendencia de Procesamiento (Últimos 7 días)", self.styles['SectionHeader']))
            chart_img = self._generate_trend_chart(stats['trend_data'])
            if chart_img:
                img = Image(chart_img, width=16*cm, height=8*cm)
                elements.append(img)
                # No eliminamos el temporal aquí porque se usa al buildear el doc
        
        elements.append(Spacer(1, 1*cm))
        
        # 4. Estadísticas por Tipo
        if stats.get('by_type'):
            elements.append(Paragraph("Documentos por Tipo", self.styles['SectionHeader']))
            type_data = [["Tipo", "Cantidad"]]
            for doc_type, count in stats['by_type'].items():
                type_data.append([doc_type, str(count)])
                
            type_table = Table(type_data, colWidths=[10*cm, 4*cm])
            type_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.hexColor('#3b82f6')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ]))
            elements.append(type_table)

        # 5. Pie de página (se añade en el build)
        doc.build(elements)
        
        return path

    def _generate_trend_chart(self, trend_data: Dict) -> Optional[str]:
        """Generar imagen de la gráfica con Matplotlib"""
        try:
            labels = trend_data.get('labels', [])
            values = trend_data.get('values', [])
            
            plt.figure(figsize=(10, 5), dpi=100)
            plt.plot(labels, values, marker='o', color='#3b82f6', linewidth=2, markersize=8)
            plt.fill_between(labels, values, color='#3b82f6', alpha=0.1)
            
            plt.title('Documentos Procesados Diariamente', fontsize=14, pad=20)
            plt.xlabel('Fecha', fontsize=10)
            plt.ylabel('Cantidad', fontsize=10)
            plt.grid(axis='y', linestyle='--', alpha=0.7)
            
            # Quitar bordes para diseño moderno
            plt.gca().spines['top'].set_visible(False)
            plt.gca().spines['right'].set_visible(False)
            
            plt.tight_layout()
            
            # Guardar en buffer
            buf = io.BytesIO()
            plt.savefig(buf, format='png')
            buf.seek(0)
            
            # Guardar a archivo temporal
            fd, img_path = tempfile.mkstemp(suffix='.png')
            os.close(fd)
            with open(img_path, 'wb') as f:
                f.write(buf.read())
            
            plt.close() # Limpiar memoria
            return img_path
        except Exception as e:
            print(f"❌ Error generando gráfica para reporte: {e}")
            return None
