from django.http import JsonResponse
from django.shortcuts import render

def health_check(request):
    return JsonResponse({"status": "ok", "service": "swiftcart"})


def service_worker(request):
    response = render(request, "service-worker.js", content_type="application/javascript")
    response["Service-Worker-Allowed"] = "/"
    response["Cache-Control"] = "no-cache"
    return response


def offline(request):
    return render(request, "offline.html")
