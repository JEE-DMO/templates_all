from typing import Dict, Any
import datetime

# ----------------------------
# 1) Générateur dynamique <table><td>
# ----------------------------

def build_environment_details_html(summary: Dict[str, Any], label: str) -> str:
    """Construit un tableau HTML type Airflow Global Summary mais dynamique."""
    html = f"""
    <h2 style="color:#003366;margin-top:30px;">📊 {label}</h2>
    <table width="100%" cellpadding="10" cellspacing="0" border="0" style="margin-top:10px;">
        <tr>
    """

    for key, stats in summary.items():
        pct = round((stats['healthy'] / stats['total']) * 100) if stats['total'] else 0
        
        if pct > 80:
            bg = "#d6f3e4"
            border = "#0f8b4b"
        else:
            bg = "#f8d7da"
            border = "#d43f3a"

        html += f"""
        <td style="background-color:{bg};border-left:4px solid {border};text-align:center;">
            <div style="font-size:32px;font-weight:bold;color:#003366;">{stats['healthy']}/{stats['total']}</div>
            <div style="color:#666;font-size:14px;">{key}</div>
        </td>
        """

    html += """
        </tr>
    </table>
    """
    return html


# ----------------------------
# 2) Génération d'un rapport complet simple
# ----------------------------

def generate_html():
    """Construit un fichier HTML pour tester l'affichage."""

    # Jeu de données de test
    sample_data_env = {
        "dev":  {"healthy": 33, "total": 34},
        "qual": {"healthy": 19, "total": 19},
        "int":  {"healthy": 1,  "total": 1},
        "uat":  {"healthy": 3,  "total": 4},  # KO mandaté (couleur rouge)
    }

    sample_data_bl = {
        "bceef":  {"healthy": 22, "total": 22},
        "pf":     {"healthy": 18, "total": 18},
        "arval":  {"healthy": 1,  "total": 1},
        "cardif": {"healthy": 3,  "total": 4},   # KO
        "embmci": {"healthy": 1,  "total": 1},
    }

    global_summary = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Airflow Health Report</title>
    </head>
    <body style="font-family:Arial, sans-serif;margin:20px;background-color:#f0f2f5;">

    <h1 style="color:#003366;border-bottom:3px solid #0f8b4b;padding-bottom:10px;">
         Airflow Health Report
    </h1>
    <p><b>Generated at:</b> {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    """

    # Ajout des blocs dynamiques
    global_summary += build_environment_details_html(sample_data_env, "Environments")
    global_summary += build_environment_details_html(sample_data_bl, "Business Lines")

    global_summary += """
    </body>
    </html>
    """

    return global_summary


# ----------------------------
# 3) Main : écrit un fichier HTML
# ----------------------------

if __name__ == "__main__":
    html_content = generate_html()
    output_file = "test_airflow_report.html"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print(f"✔ Rapport généré : {output_file}")
