from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from app.models import Customer  # adjust model name

@csrf_exempt
def delete_customer(request):
    if request.method == "POST":
        import json
        data = json.loads(request.body)
        customer_name = data.get("customer_name")

        try:
            customer = Customer.objects.get(customer_name=customer_name)
            customer.delete()
            return JsonResponse({"success": True})
        except Customer.DoesNotExist:
            return JsonResponse({"success": False, "error": "Customer not found"})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})

    return JsonResponse({"success": False, "error": "Invalid request"})
