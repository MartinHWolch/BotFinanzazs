import os
import json
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
from datetime import datetime
from typing import Dict, List

class ConsolidatedReports:
    """Genera reportes consolidados de todas las transacciones procesadas."""
    
    def __init__(self, json_dir: str = "outputs"):
        self.json_dir = json_dir
        self.transactions_df = None
    
    def load_all_transactions(self, start_date=None, end_date=None) -> pd.DataFrame:
        """
        Carga todos los JSONs procesados y los convierte en un DataFrame.
        
        Args:
            start_date: Fecha inicio para filtrar (formato: "YYYY-MM-DD")
            end_date: Fecha fin para filtrar (formato: "YYYY-MM-DD")
        """
        all_transactions = []
        
        # Buscar archivos _procesado.json
        for filename in os.listdir(self.json_dir):
            if filename.endswith("_procesado.json"):
                filepath = os.path.join(self.json_dir, filename)
                
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Extraer transacciones
                    for t in data.get('transacciones', []):
                        t['archivo_origen'] = filename
                        all_transactions.append(t)
        
        # Convertir a DataFrame
        df = pd.DataFrame(all_transactions)
        
        if not df.empty:
            # Convertir fecha a datetime
            df['fecha'] = pd.to_datetime(df['fecha'])
            
            # Filtrar por rango de fechas si se especifica
            if start_date:
                df = df[df['fecha'] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df['fecha'] <= pd.to_datetime(end_date)]
            
            # Agregar columnas útiles
            df['año'] = df['fecha'].dt.year
            df['mes'] = df['fecha'].dt.month
            df['mes_nombre'] = df['fecha'].dt.strftime('%B %Y')
            df['año_mes'] = df['fecha'].dt.to_period('M')
        
        self.transactions_df = df
        
        date_info = ""
        if start_date or end_date:
            date_info = f" (filtrado: {start_date or 'inicio'} a {end_date or 'fin'})"
        
        print(f"✅ Cargadas {len(df)} transacciones de {len(set([t['archivo_origen'] for t in all_transactions]))} archivo(s){date_info}")
        
        return df
    
    def generate_monthly_summary(self) -> pd.DataFrame:
        """Genera resumen mensual de ingresos, egresos y balance."""
        if self.transactions_df is None or self.transactions_df.empty:
            return pd.DataFrame()
        
        # Agrupar por mes
        monthly = self.transactions_df.groupby(['año_mes', 'tipo'])['monto'].sum().unstack(fill_value=0)
        
        # Calcular balance
        if 'ingreso' not in monthly.columns:
            monthly['ingreso'] = 0
        if 'egreso' not in monthly.columns:
            monthly['egreso'] = 0
        
        monthly['balance'] = monthly.get('ingreso', 0) - monthly.get('egreso', 0)
        monthly['balance_acumulado'] = monthly['balance'].cumsum()
        
        return monthly
    
    def generate_charts(self, output_dir: str = "outputs/reportes"):
        """Genera gráficos de análisis financiero."""
        os.makedirs(output_dir, exist_ok=True)
        
        monthly = self.generate_monthly_summary()
        
        if monthly.empty:
            print("⚠️  No hay datos para generar gráficos")
            return
        
        # Configuración de estilo
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # 1. Ingresos vs Egresos por mes
        fig, ax = plt.subplots(figsize=(12, 6))
        x = range(len(monthly))
        width = 0.35
        
        ax.bar([i - width/2 for i in x], monthly.get('ingreso', 0), width, label='Ingresos', color='#4CAF50')
        ax.bar([i + width/2 for i in x], monthly.get('egreso', 0), width, label='Egresos', color='#F44336')
        
        ax.set_xlabel('Mes')
        ax.set_ylabel('Monto ($)')
        ax.set_title('Ingresos vs Egresos por Mes', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels([str(p) for p in monthly.index], rotation=45, ha='right')
        ax.legend()
        ax.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'ingresos_vs_egresos.png'), dpi=100)
        plt.close()
        
        # 2. Balance mensual (líneas)
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(range(len(monthly)), monthly['balance'], marker='o', linewidth=2, color='#2196F3', label='Balance Mensual')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        ax.set_xlabel('Mes')
        ax.set_ylabel('Balance ($)')
        ax.set_title('Balance Mensual', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(monthly)))
        ax.set_xticklabels([str(p) for p in monthly.index], rotation=45, ha='right')
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'balance_mensual.png'), dpi=100)
        plt.close()
        
        # 3. Balance acumulado
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.fill_between(range(len(monthly)), monthly['balance_acumulado'], alpha=0.3, color='#9C27B0')
        ax.plot(range(len(monthly)), monthly['balance_acumulado'], marker='o', linewidth=2, color='#9C27B0', label='Balance Acumulado')
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5)
        
        ax.set_xlabel('Mes')
        ax.set_ylabel('Balance Acumulado ($)')
        ax.set_title('Evolución del Balance Acumulado', fontsize=14, fontweight='bold')
        ax.set_xticks(range(len(monthly)))
        ax.set_xticklabels([str(p) for p in monthly.index], rotation=45, ha='right')
        ax.legend()
        ax.grid(alpha=0.3)
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'balance_acumulado.png'), dpi=100)
        plt.close()
        
        # 4. Top 10 Gastos
        top_gastos = self.transactions_df[self.transactions_df['tipo'] == 'egreso'].nlargest(10, 'monto')
        
        if not top_gastos.empty:
            fig, ax = plt.subplots(figsize=(10, 6))
            colors = plt.cm.Reds(range(10, 0, -1))
            ax.barh(range(len(top_gastos)), top_gastos['monto'], color=colors)
            ax.set_yticks(range(len(top_gastos)))
            ax.set_yticklabels([f"{desc[:30]}..." if len(desc) > 30 else desc for desc in top_gastos['descripcion']], fontsize=9)
            ax.set_xlabel('Monto ($)')
            ax.set_title('Top 10 Gastos Más Grandes', fontsize=14, fontweight='bold')
            ax.invert_yaxis()
            ax.grid(axis='x', alpha=0.3)
            
            # Agregar valores
            for i, v in enumerate(top_gastos['monto']):
                ax.text(v, i, f' ${v:,.0f}', va='center', fontsize=9)
            
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, 'top_gastos.png'), dpi=100)
            plt.close()
        
        print(f"✅ Gráficos generados en: {output_dir}/")
    
    def generate_html_report(self, output_path: str = "outputs/reportes/reporte_consolidado.html"):
        """Genera reporte HTML consolidado con todos los análisis."""
        monthly = self.generate_monthly_summary()
        
        if monthly.empty:
            print("⚠️  No hay datos para generar reporte")
            return
        
        # Calcular totales generales
        total_ingresos = monthly.get('ingreso', 0).sum()
        total_egresos = monthly.get('egreso', 0).sum()
        balance_final = total_ingresos - total_egresos
        
        balance_color = '#4CAF50' if balance_final >= 0 else '#F44336'
        
        # HTML
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte Financiero Consolidado</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .card h3 {{
            margin-top: 0;
            color: #666;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .card .value {{
            font-size: 32px;
            font-weight: bold;
            margin: 10px 0;
        }}
        .income {{ color: #4CAF50; }}
        .expense {{ color: #F44336; }}
        .balance {{ color: {balance_color}; }}
        .charts {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .chart-container {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .chart-container img {{
            width: 100%;
            height: auto;
        }}
        table {{
            width: 100%;
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-collapse: collapse;
            margin-bottom: 30px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #f0f0f0;
        }}
        tr:hover {{
            background: #f9f9f9;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Reporte Financiero Consolidado 2025</h1>
        <p>Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p>Total de transacciones: {len(self.transactions_df)}</p>
    </div>

    <div class="summary">
        <div class="card">
            <h3>💰 Ingresos Totales</h3>
            <div class="value income">${total_ingresos:,.0f}</div>
        </div>
        <div class="card">
            <h3>💸 Egresos Totales</h3>
            <div class="value expense">${total_egresos:,.0f}</div>
        </div>
        <div class="card">
            <h3>📈 Balance Final</h3>
            <div class="value balance">${balance_final:,.0f}</div>
        </div>
    </div>

    <div class="charts">
        <div class="chart-container">
            <h2>Ingresos vs Egresos</h2>
            <img src="ingresos_vs_egresos.png" alt="Ingresos vs Egresos">
        </div>
        <div class="chart-container">
            <h2>Balance Mensual</h2>
            <img src="balance_mensual.png" alt="Balance Mensual">
        </div>
        <div class="chart-container">
            <h2>Balance Acumulado</h2>
            <img src="balance_acumulado.png" alt="Balance Acumulado">
        </div>
        <div class="chart-container">
            <h2>Top 10 Gastos</h2>
            <img src="top_gastos.png" alt="Top Gastos">
        </div>
    </div>

    <div class="card">
        <h2>📅 Resumen Mensual</h2>
        <table>
            <thead>
                <tr>
                    <th>Mes</th>
                    <th>Ingresos</th>
                    <th>Egresos</th>
                    <th>Balance</th>
                    <th>Balance Acumulado</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for periodo, row in monthly.iterrows():
            html += f"""
                <tr>
                    <td>{periodo}</td>
                    <td style="color: #4CAF50;">${row.get('ingreso', 0):,.0f}</td>
                    <td style="color: #F44336;">${row.get('egreso', 0):,.0f}</td>
                    <td style="color: {'#4CAF50' if row['balance'] >= 0 else '#F44336'};">${row['balance']:,.0f}</td>
                    <td style="color: {'#4CAF50' if row['balance_acumulado'] >= 0 else '#F44336'};">${row['balance_acumulado']:,.0f}</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p>Generado automáticamente por Financial Bot 🤖</p>
    </div>
</body>
</html>
"""
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        print(f"✅ Reporte HTML generado: {output_path}")
    
    def generate_all_reports(self):
        """Genera todos los reportes consolidados."""
        print("\n📊 Generando reportes consolidados...\n")
        
        # Cargar fechas de configuración
        from config import REPORT_START_DATE, REPORT_END_DATE
        
        # Cargar datos
        self.load_all_transactions(start_date=REPORT_START_DATE, end_date=REPORT_END_DATE)
        
        if self.transactions_df is None or self.transactions_df.empty:
            print("❌ No hay transacciones para reportar")
            return
        
        # Generar gráficos
        self.generate_charts()
        
        # Generar HTML
        self.generate_html_report()
        
        print(f"\n{'='*60}")
        print("✅ Reportes generados exitosamente")
        print("   📂 Ubicación: outputs/reportes/")
        print("   📄 Abrir: outputs/reportes/reporte_consolidado.html")
        print(f"{'='*60}\n")


if __name__ == "__main__":
    reports = ConsolidatedReports()
    reports.generate_all_reports()
