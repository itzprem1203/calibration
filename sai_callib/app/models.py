from django.db import models


# Customer model
class Customer(models.Model):
    customer_name = models.CharField(max_length=255)
    primary_contact_person = models.CharField(max_length=255)
    secondary_contact_person = models.CharField(max_length=255)
    primary_email = models.EmailField()
    secondary_email = models.EmailField()
    primary_phone_no = models.CharField(max_length=15)
    secondary_phone_no = models.CharField(max_length=15)
    gst_no = models.CharField(max_length=50)
    primary_dept = models.CharField(max_length=255)
    secondary_dept = models.CharField(max_length=255)
    address = models.TextField()

# Setting Plug Trace model
class SettingPlugTrace(models.Model):
    master_name = models.CharField(max_length=255)
    id_no = models.CharField(max_length=50)
    calibration_report_no = models.CharField(max_length=50)
    valid_upto = models.CharField(max_length=50)
    traceability = models.TextField()

# Setting Ring Trace model
class SettingRingTrace(models.Model):
    master_name = models.CharField(max_length=255)
    id_no = models.CharField(max_length=50)
    calibration_report_no = models.CharField(max_length=50)
    valid_upto = models.CharField(max_length=50)
    traceability = models.TextField()

# Setting Plug Master model
class SettingPlugMaster(models.Model):
    parameter_name = models.CharField(max_length=255)
    ref_size = models.CharField(max_length=50)
    nominal = models.CharField(max_length=50)

# Setting Ring Master model
class SettingRingMaster(models.Model):
    parameter_name = models.CharField(max_length=255)
    ref_size = models.CharField(max_length=50)
    nominal = models.CharField(max_length=50)

# Engineer Manager Details model
class EngineerManagerDetails(models.Model):
    calib_engineer = models.CharField(max_length=255)
    quality_manager = models.CharField(max_length=255)
    certificate_no = models.CharField(max_length=50)

class WorkOrder(models.Model):
    customer_name = models.CharField(max_length=255)
    wo_date = models.CharField(max_length=50)  # Work Order Date
    work_order_no = models.CharField(max_length=50)
    customer_po_no = models.CharField(max_length=50, blank=True, null=True)
    customer_ref_date = models.CharField(max_length=50,blank=True, null=True)
    order_type = models.CharField(max_length=100, blank=True, null=True)
    customer_address = models.TextField(blank=True, null=True)
    inward_no = models.CharField(max_length=255)
    item = models.CharField(max_length=255)
    hsn = models.CharField(max_length=100, blank=True, null=True)
    sr_no = models.CharField(max_length=100, blank=True, null=True)  # Serial number
    id_no = models.CharField(max_length=100, blank=True, null=True)  # ID number
    range = models.CharField(max_length=100, blank=True, null=True)
    make = models.CharField(max_length=100, blank=True, null=True)
    channels = models.CharField(max_length=255)
    



class MainCalibration(models.Model):
    certificate_num = models.CharField(max_length=100, unique=True)
    work_order = models.CharField(max_length=100)
    date_of_issue = models.DateField(null=True, blank=True)
    date_of_calibration = models.DateField(null=True, blank=True)
    next_calibration = models.DateField(null=True, blank=True)
    customer_address = models.TextField(blank=True)
    range = models.CharField(max_length=100, blank=True)
    least_count = models.CharField(max_length=100, blank=True)
    identification_no = models.CharField(max_length=100, blank=True)
    si_no = models.CharField(max_length=100, blank=True)
    make = models.CharField(max_length=100, blank=True)
    customer_ref = models.CharField(max_length=100, blank=True)
    date_calib = models.DateField(null=True, blank=True)
    date_of_receipt = models.DateField(null=True, blank=True)
    calib_procedure_no = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=100, blank=True)
    inward_no = models.CharField(max_length=100, blank=True)
    environment = models.CharField(max_length=100, blank=True)
    uncertainty = models.CharField(max_length=100, blank=True)
    calib_engineer = models.CharField(max_length=100, blank=True)
    quality_manager = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.certificate_num} - {self.work_order}"

class CalibrationEquipment(models.Model):
    main_calibration = models.ForeignKey(MainCalibration, related_name='equipments', on_delete=models.CASCADE)
    sr_no = models.IntegerField()
    master_name = models.CharField(max_length=100, blank=True)
    id_no = models.CharField(max_length=100, blank=True)
    calibration_no = models.CharField(max_length=100, blank=True)
    valid_upto = models.CharField(max_length=100, blank=True)
    traceability = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Equipment {self.sr_no} for {self.main_calibration.certificate_num}"

class CalibrationResult(models.Model):
    main_calibration = models.ForeignKey(MainCalibration, related_name='results', on_delete=models.CASCADE)
    container_id = models.CharField(max_length=50)
    parameter = models.CharField(max_length=100, blank=True)
    ref_size = models.CharField(max_length=100, blank=True)
    nominal = models.CharField(max_length=100, blank=True)
    observation_size = models.CharField(max_length=100, blank=True)
    error = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Result for {self.main_calibration.certificate_num} - {self.container_id}"


class InterlinkData(models.Model):
    Date_Time = models.DateTimeField() 
    PartModel = models.CharField(max_length=50)
    CompSrNo = models.CharField(max_length=150)
    CompResultStatus = models.CharField(max_length=50)


    class Meta:
        app_label = 'client_app'
        managed = False   # 🚨 very important, Django will not try to create/migrate this table
        db_table = 'app_interlinkdata'   # 🔥 your exact table name


# Setting Ring Trace model
class LVDTprobeTrace(models.Model):
    master_name = models.CharField(max_length=255)
    id_no = models.CharField(max_length=50)
    calibration_report_no = models.CharField(max_length=50)
    valid_upto = models.CharField(max_length=50)
    traceability = models.TextField()

# Setting Plug Master model
class LVDTprobeMaster(models.Model):
    parameter_name = models.CharField(max_length=255)
    ref_size = models.CharField(max_length=50)
    