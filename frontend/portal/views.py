import requests
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from . import db


def home(request):
    return render(request, 'portal/home.html')


def customers(request):
    rows = db.query("""
        SELECT client_id, ville, etat
        FROM clients
        ORDER BY client_id
        LIMIT 100
    """)
    return render(request, 'portal/customers.html', {'customers': rows})


def reports(request):
    rows = db.query("""
        SELECT table_name, table_rows, create_time
        FROM information_schema.tables
        WHERE table_schema = 'ynov-db'
        ORDER BY create_time DESC
    """)
    return render(request, 'portal/reports.html', {'reports': rows})


@login_required
def dashboard(request):
    stats = db.query_one("""
        SELECT
            (SELECT COUNT(*) FROM clients)   AS nb_clients,
            (SELECT COUNT(*) FROM commandes) AS nb_commandes,
            (SELECT COUNT(*) FROM produits)  AS nb_produits,
            (SELECT COUNT(*) FROM vendeurs)  AS nb_vendeurs,
            (SELECT COUNT(*) FROM paiements) AS nb_paiements,
            (SELECT COUNT(*) FROM avis)      AS nb_avis
    """)
    top_categories = db.query("""
        SELECT pr.categorie,
               COUNT(*)               AS nb_ventes,
               ROUND(SUM(ac.prix), 2) AS revenus_total
        FROM articles_commande ac
        JOIN produits pr ON ac.produit_id = pr.produit_id
        WHERE pr.categorie IS NOT NULL
        GROUP BY pr.categorie
        ORDER BY nb_ventes DESC
        LIMIT 5
    """)
    return render(request, 'portal/dashboard.html', {
        'stats': stats,
        'top_categories': top_categories,
    })


def upload(request):
    if request.method == 'POST':
        csv_file = request.FILES.get('csv_file')

        if not csv_file:
            messages.error(request, 'Aucun fichier sélectionné.')
            return redirect('upload')

        if not csv_file.name.lower().endswith(('.csv', '.json')):
            messages.error(request, f"'{csv_file.name}' : seuls les fichiers .csv et .json sont acceptés.")
            return redirect('upload')

        try:
            response = requests.post(
                f"{settings.FLASK_API_URL}/olist/upload",
                files={'file': (csv_file.name, csv_file.read(), 'text/csv')},
                timeout=60,
            )
            data = response.json()
            if response.ok:
                nb_cols = len(data.get('colonnes', []))
                messages.success(
                    request,
                    f"Import réussi — table '{data['table']}' créée avec {nb_cols} colonnes, "
                    f"{data['lignes']} lignes insérées."
                )
            else:
                messages.error(request, f"Échec : {data.get('message', 'Erreur inconnue')}")

        except requests.ConnectionError:
            messages.error(request, "Impossible de joindre l'API Flask. Vérifiez que python app.py tourne sur le port 5000.")
        except Exception as e:
            messages.error(request, f"Erreur inattendue : {str(e)}")

        return redirect('upload')

    return render(request, 'portal/upload.html')
