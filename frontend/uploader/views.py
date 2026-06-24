import requests
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect


def upload(request):
    if request.method == "POST":
        csv_file = request.FILES.get("csv_file")

        if not csv_file:
            messages.error(request, "Aucun fichier selectionne.")
            return redirect("upload")

        allowed = (".csv", ".json")
        if not csv_file.name.lower().endswith(allowed):
            messages.error(request, f"'{csv_file.name}' : seuls les fichiers .csv et .json sont acceptés.")
            return redirect("upload")

        try:
            response = requests.post(
                f"{settings.FLASK_API_URL}/olist/upload",
                files={"file": (csv_file.name, csv_file.read(), "text/csv")},
                timeout=60,
            )
            data = response.json()

            if response.ok:
                nb_cols = len(data.get("colonnes", []))
                messages.success(
                    request,
                    f"Import reussi — table '{data['table']}' créée avec {nb_cols} colonnes, "
                    f"{data['lignes']} lignes insérées."
                )
            else:
                messages.error(request, f"Echec : {data.get('message', 'Erreur inconnue')}")

        except requests.ConnectionError:
            messages.error(request, "Impossible de joindre l'API Flask. Verifiez que python app.py tourne sur le port 5000.")
        except Exception as e:
            messages.error(request, f"Erreur inattendue : {str(e)}")

        return redirect("upload")

    return render(request, "uploader/index.html")
