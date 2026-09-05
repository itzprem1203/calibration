import json
import re
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from app.models import Customer, MainCalibration, WorkOrder


@csrf_exempt
def inward(request):
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        if customer_name:
            work_orders = WorkOrder.objects.filter(customer_name=customer_name).distinct().values('work_order_no')
            work_order_list = list(work_orders)
            return JsonResponse(work_order_list, safe=False)

        try:
            data = json.loads(request.body)
            print("The value get from the front end:", data)
            customer_name = data.get('customerName')
            wo_date = data.get('woDate')
            work_order_no = data.get('workOrderNo')
            customer_po_no = data.get('customerPoNo')
            customer_ref_date = data.get('customerRefDate')
            order_type = data.get('orderType')
            customer_address = data.get('customerAddress')

            if not all([customer_name, wo_date, work_order_no]):
                return JsonResponse({'error': 'Missing required fields.'}, status=400)

            items = data.get('items', [])
            saved_items = []
            skipped_items = []

            for item in items:
                sr_no = item.get('srNo')
                id_no = item.get('idNo')
                inward_no = item.get('inward_no')
                
                if sr_no and id_no:
                    # Check if inward_no exists
                    existing_work_order = WorkOrder.objects.filter(inward_no=inward_no).first()

                    if existing_work_order:
                        # Update the existing work order
                        existing_work_order.customer_name = customer_name
                        existing_work_order.wo_date = wo_date
                        existing_work_order.work_order_no = work_order_no
                        existing_work_order.customer_po_no = customer_po_no
                        existing_work_order.customer_ref_date = customer_ref_date
                        existing_work_order.order_type = order_type
                        existing_work_order.customer_address = customer_address
                        existing_work_order.item = item.get('item')
                        existing_work_order.hsn = item.get('hsn')
                        existing_work_order.sr_no = sr_no
                        existing_work_order.id_no = id_no
                        existing_work_order.range = item.get('range')
                        existing_work_order.make = item.get('make')
                        existing_work_order.channels = item.get('channels')
                        existing_work_order.save()  # Save the updated object
                        saved_items.append(existing_work_order.id)  # Optionally collect the IDs of updated records
                    else:
                        # If it doesn't exist, create a new work order
                        work_order = WorkOrder.objects.create(
                            customer_name=customer_name,
                            wo_date=wo_date,
                            work_order_no=work_order_no,
                            customer_po_no=customer_po_no,
                            customer_ref_date=customer_ref_date,
                            order_type=order_type,
                            customer_address=customer_address,
                            inward_no=inward_no,
                            item=item.get('item'),
                            hsn=item.get('hsn'),
                            sr_no=sr_no,
                            id_no=id_no,
                            range=item.get('range'),
                            make=item.get('make'),
                            channels=item.get('channels')
                        )
                        saved_items.append(work_order.id)

            return JsonResponse({
                'message': 'Work order processed successfully!',
                'saved_items': saved_items,
                'skipped_items': skipped_items
            })

        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)




    elif request.method == 'GET':
        if 'generate_inward_no' in request.GET:
            last_work_order = WorkOrder.objects.order_by('-inward_no').first()
            if last_work_order:
                last_inward_no = last_work_order.inward_no
                match = re.match(r"(SAI/CAL/\d{2}-\d{2}/)(\d+)", last_inward_no)
                if match:
                    prefix = match.group(1)
                    number = int(match.group(2)) + 1
                    new_inward_no = f"{prefix}{number:03d}"
                else:
                    new_inward_no = "SAI/CAL/24-25/001"
            else:
                new_inward_no = "SAI/CAL/24-25/001"
            
            return JsonResponse({'new_inward_no': new_inward_no})
        # Check if we are fetching work order details based on work order number
        work_order_no = request.GET.get('work_order_no')  # Fetch work order number from GET request

        if work_order_no:  # If work order number is provided, fetch related data
            try:
                # Fetch all work orders with the provided work order number
                work_orders = WorkOrder.objects.filter(work_order_no=work_order_no)

                if not work_orders.exists():
                    return JsonResponse({'success': False, 'error': 'Work order not found.'})

                # Prepare response data
                data = {
                    'success': True,
                    'wo_date': work_orders.first().wo_date,  # Assuming wo_date is the same for all items
                    'customer_po_no': work_orders.first().customer_po_no,
                    'customer_ref_date': work_orders.first().customer_ref_date,
                    'order_type': work_orders.first().order_type,
                    'customer_address': work_orders.first().customer_address,
                    'items': []
                }

                # Loop through each work order item and append it to the items list
                for work_order in work_orders:
                    is_in_main_calibration = MainCalibration.objects.filter(inward_no=work_order.inward_no).exists()
                    data['items'].append({
                        'inward_no': work_order.inward_no,
                        'item': work_order.item,
                        'hsn': work_order.hsn,
                        'sr_no': work_order.sr_no,
                        'id_no': work_order.id_no,
                        'range': work_order.range,
                        'make': work_order.make,
                        'channels': work_order.channels,
                        'is_in_main_calibration': is_in_main_calibration
                    })

                return JsonResponse(data)

            except Exception as e:
                return JsonResponse({'success': False, 'error': str(e)})

        # Fetch all Customer objects to pass them to the template for normal GET requests
        customer_value = Customer.objects.all()

        # Render the form with the customer data
        context = {
            'customer_value': customer_value,
        }
        return render(request, "app/inward.html", context)
    
    elif request.method == 'DELETE':
        try:
            # Parse the request body to get the work order ID
            data = json.loads(request.body)
            work_order_id = data.get('work_order_id')
            print("work_order_id",work_order_id)

            if not work_order_id:
                return JsonResponse({'success': False, 'error': 'Missing work order ID.'}, status=400)

            print("Attempting to delete work order with ID:", work_order_id)  # Debug print

            # Find and delete the work order
            work_order = WorkOrder.objects.get(inward_no=work_order_id)
            work_order.delete()

            return JsonResponse({'success': True, 'message': 'Work order deleted successfully!'})

        except WorkOrder.DoesNotExist:
            print("Work order not found with ID:", work_order_id)  # Debug print
            return JsonResponse({'success': False, 'error': 'Work order not found.'}, status=404)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON format.'}, status=400)
        except Exception as e:
            print("Error during deletion:", e)  # Debug print
            return JsonResponse({'success': False, 'error': str(e)}, status=500)



    return JsonResponse({'success': False, 'error': 'Invalid request method.'}, status=405)

