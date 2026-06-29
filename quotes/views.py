import json
import random
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .models import Quote
from django.shortcuts import render
from django.http import HttpResponse




# ✅ GET all quoteshttps://www.pythonanywhere.com/user/mynewnokiap8/files/home/mynewnokiap8/whatsappcalories/quotes
def quotes_api(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    quotes = Quote.objects.all().order_by("-created_at")
    data = [quote.to_dict() for quote in quotes]
    return JsonResponse(data, safe=False)


# ✅ GET random quote
def random_quote_api(request):
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    quote = Quote.objects.order_by("?").first()

    if not quote:
        return JsonResponse({"error": "No quotes available"}, status=404)

    return HttpResponse(f"{quote}")



def dashBoard(request):
    if request.method == "GET":
        return render(request, "quotes/session_dashboard.html")

def add_quote_api(request):
    if request.method == "GET":
        return render(request, "quotes/add_quote.html")

    if request.method == "POST":
        quote_text = request.POST.get("quote")
        password = request.POST.get("password")

        if not quote_text or not password:
            return HttpResponse("Both fields are required", status=400)

        if password != settings.QUOTE_API_PASSWORD:
            return HttpResponse("Invalid password", status=403)

        Quote.objects.create(
            text=quote_text
        )

        return HttpResponse("Quote added successfully ✅")

    return HttpResponse("Method not allowed", status=405)

