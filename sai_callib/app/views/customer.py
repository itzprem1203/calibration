
import json
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from app.models import Customer, EngineerManagerDetails

@csrf_exempt
def customer(request):
    if request.method == 'POST':
        try:
            # Parse JSON data from the request
            data = json.loads(request.body)
            form_type = data.get('formType')
            form_data = data.get('formData')

            print("form_type",form_type)
            print("form_data",form_data)
            
            if form_type == 'customer':
                # Check if a customer with the given name already exists
                customer, created = Customer.objects.update_or_create(
                    customer_name=form_data['customer_name'],  # Use a unique field to identify the customer
                    defaults={
                        'primary_contact_person': form_data['primary_contact_person'],
                        'secondary_contact_person': form_data['secondary_contact_person'],
                        'primary_email': form_data['primary_email'],
                        'secondary_email': form_data['secondary_email'],
                        'primary_phone_no': form_data['primary_phone_no'],
                        'secondary_phone_no': form_data['secondary_phone_no'],
                        'gst_no': form_data['gst_no'],
                        'primary_dept': form_data['primary_dept'],
                        'secondary_dept': form_data['secondary_dept'],
                        'address': form_data['address']
                    }
                )

                if created:
                    message = 'New customer created successfully.'
                else:
                    message = 'Customer updated successfully.'

           
            elif form_type == 'engineer_manager_details':
                # Save or update engineer_manager_details table data
                for row in form_data['rows']:
                    row_id = row.get('id')  # Assuming each row has a unique ID
                    if row_id:
                        obj = EngineerManagerDetails.objects.get(id=row_id)
                        obj.calib_engineer = row['calibEngineer']
                        obj.quality_manager = row['qualityManager']
                        obj.certificate_no = row['certificateNo']
                        obj.save()
                    else:
                        EngineerManagerDetails.objects.create(
                            calib_engineer=row['calibEngineer'],
                            quality_manager=row['qualityManager'],
                            certificate_no=row['certificateNo']
                        )

            return JsonResponse({'status': 'success', 'message': 'Data saved successfully.'})

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
        
    elif request.method == 'GET':
        customer_value = Customer.objects.all()
      
        EngineerManagerDetails_value = EngineerManagerDetails.objects.all()

        context ={
            'customer_value': customer_value, 
           
            'EngineerManagerDetails_value' : EngineerManagerDetails_value
        }

    elif request.method == 'DELETE':
        try:
            # Parse the JSON data from the request body
            data = json.loads(request.body)
            form_type = data.get('formType')
            ids_to_delete = data.get('idsToDelete', [])

           

            if form_type == 'tableBody-5':
                # Delete engineer_manager_details records
                EngineerManagerDetails.objects.filter(id__in=ids_to_delete).delete()

            else:
                return JsonResponse({'error': 'Invalid form type'}, status=400)

            return JsonResponse({'success': True, 'message': 'Data deleted successfully'})

        except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON'}, status=400)

   
    
    return render(request,"app/customer.html",context)

