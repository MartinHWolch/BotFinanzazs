import json
import os
from datetime import datetime
from typing import List, Dict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI para generar gráficos

class ReportGenerator:
    def __init__(self, outputs_dir="outputs"):
        self.outputs_dir = outputs_dir
    
    def load_all_reports(self) -> List[Dict]:
        """Load all processed JSON reports from outputs directory."""
        reports = []
        if not os.path.exists(self.outputs_dir):
            return reports
        
        for filename in os.listdir(self.outputs_dir):
            if filename.endswith("_processed.json"):
                filepath = os.path.join(self.outputs_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    data['source_file'] = filename
                    reports.append(data)
        
        return reports
    
    def generate_consolidated_report(self):
        """Generate a consolidated HTML report with all data and charts."""
        reports = self.load_all_reports()
        
        if not reports:
            print("No processed reports found to analyze.")
            return
        
        print(f"\n📊 Generating consolidated report from {len(reports)} file(s)...")
        
        # Aggregate all transactions
        all_transactions = []
        total_income = 0
        total_expense = 0
        
        for report in reports:
            all_transactions.extend(report['transactions'])
            total_income += report['summary']['total_income']
            total_expense += report['summary']['total_expense']
        
        # Analyze by category
        category_totals = {}
        for t in all_transactions:
            if t['type'] == 'egreso':
                category = t['category']
                category_totals[category] = category_totals.get(category, 0) + t['amount']
        
        # Sort categories by amount
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        # Generate charts
        self._generate_pie_chart(sorted_categories)
        self._generate_bar_chart(total_income, total_expense)
        
        # Top 5 expenses
        top_expenses = sorted(
            [t for t in all_transactions if t['type'] == 'egreso'],
            key=lambda x: x['amount'],
            reverse=True
        )[:5]
        
        # Generate HTML report
        html_content = self._create_html_report(
            reports=reports,
            total_income=total_income,
            total_expense=total_expense,
            category_totals=sorted_categories,
            top_expenses=top_expenses
        )
        
        # Save HTML
        report_path = os.path.join(self.outputs_dir, f"consolidated_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✅ Report generated: {report_path}")
        print(f"\n📈 Summary:")
        print(f"  Total Income:  ${total_income:,.0f}")
        print(f"  Total Expense: ${total_expense:,.0f}")
        print(f"  Balance:       ${total_income - total_expense:,.0f}")
        print(f"\n🏷️ Top 3 Categories:")
        for i, (cat, amount) in enumerate(sorted_categories[:3], 1):
            percentage = (amount / total_expense * 100) if total_expense > 0 else 0
            print(f"  {i}. {cat}: ${amount:,.0f} ({percentage:.1f}%)")
    
    def _generate_pie_chart(self, category_totals):
        """Generate pie chart for expenses by category."""
        if not category_totals:
            return
        
        labels = [cat for cat, _ in category_totals]
        sizes = [amount for _, amount in category_totals]
        
        # Limit to top 8 + "Others"
        if len(labels) > 8:
            others_sum = sum(sizes[8:])
            labels = labels[:8] + ['Otros']
            sizes = sizes[:8] + [others_sum]
        
        plt.figure(figsize=(10, 7))
        plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        plt.title('Gastos por Categoría', fontsize=16, fontweight='bold')
        plt.axis('equal')
        
        chart_path = os.path.join(self.outputs_dir, 'chart_categories.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=100)
        plt.close()
    
    def _generate_bar_chart(self, total_income, total_expense):
        """Generate bar chart comparing income vs expenses."""
        categories = ['Ingresos', 'Egresos']
        values = [total_income, total_expense]
        colors = ['#4CAF50', '#F44336']
        
        plt.figure(figsize=(8, 6))
        bars = plt.bar(categories, values, color=colors, width=0.5)
        plt.title('Ingresos vs Egresos', fontsize=16, fontweight='bold')
        plt.ylabel('Monto ($)', fontsize=12)
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                    f'${height:,.0f}',
                    ha='center', va='bottom', fontsize=11)
        
        chart_path = os.path.join(self.outputs_dir, 'chart_income_expense.png')
        plt.savefig(chart_path, bbox_inches='tight', dpi=100)
        plt.close()
    
    def _create_html_report(self, reports, total_income, total_expense, category_totals, top_expenses):
        """Create HTML content for the consolidated report."""
        balance = total_income - total_expense
        balance_color = '#4CAF50' if balance >= 0 else '#F44336'
        
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
            max-width: 1200px;
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
            color: #333;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 1px;
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
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
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
        <h1>📊 Reporte Financiero Consolidado</h1>
        <p>Generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</p>
        <p>Total de reportes procesados: {len(reports)}</p>
    </div>

    <div class="summary">
        <div class="card">
            <h3>💰 Ingresos Totales</h3>
            <div class="value income">${total_income:,.0f}</div>
        </div>
        <div class="card">
            <h3>💸 Egresos Totales</h3>
            <div class="value expense">${total_expense:,.0f}</div>
        </div>
        <div class="card">
            <h3>📈 Balance</h3>
            <div class="value balance">${balance:,.0f}</div>
        </div>
    </div>

    <div class="charts">
        <div class="chart-container">
            <h2>Distribución de Gastos</h2>
            <img src="chart_categories.png" alt="Gastos por Categoría">
        </div>
        <div class="chart-container">
            <h2>Comparación General</h2>
            <img src="chart_income_expense.png" alt="Ingresos vs Egresos">
        </div>
    </div>

    <div class="card" style="margin-bottom: 30px;">
        <h2>🏷️ Gastos por Categoría</h2>
        <table>
            <thead>
                <tr>
                    <th>Categoría</th>
                    <th>Monto</th>
                    <th>% del Total</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for category, amount in category_totals:
            percentage = (amount / total_expense * 100) if total_expense > 0 else 0
            html += f"""
                <tr>
                    <td>{category}</td>
                    <td>${amount:,.0f}</td>
                    <td>{percentage:.1f}%</td>
                </tr>
"""
        
        html += """
            </tbody>
        </table>
    </div>

    <div class="card">
        <h2>🔝 Top 5 Gastos</h2>
        <table>
            <thead>
                <tr>
                    <th>Fecha</th>
                    <th>Descripción</th>
                    <th>Categoría</th>
                    <th>Monto</th>
                </tr>
            </thead>
            <tbody>
"""
        
        for expense in top_expenses:
            html += f"""
                <tr>
                    <td>{expense['date']}</td>
                    <td>{expense['description'][:50]}...</td>
                    <td>{expense['category']}</td>
                    <td>${expense['amount']:,.0f}</td>
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
        return html
