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
            customer_name = (data.get('customerName') or '').strip()
            wo_date = (data.get('woDate') or '').strip()
            work_order_no = (data.get('workOrderNo') or '').strip()
            customer_po_no = data.get('customerPoNo') or ''
            customer_ref_date = data.get('customerRefDate') or ''
            order_type = data.get('orderType') or ''
            customer_address = data.get('customerAddress') or ''

            missing = []
            if not customer_name:
                missing.append('customer name')
            if not wo_date:
                missing.append('WO date')
            if not work_order_no:
                missing.append('work order no')
            if missing:
                return JsonResponse(
                    {'error': 'Missing required fields: ' + ', '.join(missing)},
                    status=400,
                )

            items = data.get('items', [])
            if not items:
                return JsonResponse({'error': 'Add at least one item row before saving.'}, status=400)

            saved_items = []
            skipped_items = []

            for item in items:
                sr_no = item.get('srNo') or ''
                id_no = item.get('idNo') or ''
                inward_no = item.get('inward_no') or ''
                item_name = item.get('item') or ''
                hsn = item.get('hsn') or ''
                range_val = item.get('range') or ''
                make = item.get('make') or ''
                channels = item.get('channels') or ''

                # Require identifying fields for a real line item
                if not (sr_no and id_no):
                    skipped_items.append({'srNo': sr_no, 'idNo': id_no, 'reason': 'missing srNo/idNo'})
                    continue
                if not inward_no:
                    return JsonResponse(
                        {'error': 'Inward No is missing on one or more rows. Create/generate inward numbers first.'},
                        status=400,
                    )

                existing_work_order = WorkOrder.objects.filter(inward_no=inward_no).first()

                if existing_work_order:
                    existing_work_order.customer_name = customer_name
                    existing_work_order.wo_date = wo_date
                    existing_work_order.work_order_no = work_order_no
                    existing_work_order.customer_po_no = customer_po_no
                    existing_work_order.customer_ref_date = customer_ref_date
                    existing_work_order.order_type = order_type
                    existing_work_order.customer_address = customer_address
                    existing_work_order.item = item_name
                    existing_work_order.hsn = hsn
                    existing_work_order.sr_no = sr_no
                    existing_work_order.id_no = id_no
                    existing_work_order.range = range_val
                    existing_work_order.make = make
                    existing_work_order.channels = channels
                    existing_work_order.save()
                    saved_items.append(existing_work_order.id)
                else:
                    work_order = WorkOrder.objects.create(
                        customer_name=customer_name,
                        wo_date=wo_date,
                        work_order_no=work_order_no,
                        customer_po_no=customer_po_no,
                        customer_ref_date=customer_ref_date,
                        order_type=order_type,
                        customer_address=customer_address,
                        inward_no=inward_no,
                        item=item_name,
                        hsn=hsn,
                        sr_no=sr_no,
                        id_no=id_no,
                        range=range_val,
                        make=make,
                        channels=channels,
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

