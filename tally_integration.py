import frappe
import requests
import xml.etree.ElementTree as ET
from datetime import datetime

tally_settings = frappe.get_doc("Tally Integration Settings")
tally_url = tally_settings.tally_url 

@frappe.whitelist()
def send_students_to_tally(doc, method):  
    try:
        student = doc.as_dict()  
        students = [student]  

        tally_xml = convert_to_tally_ledger_xml(students)

        headers = {"Content-Type": "text/xml"}
        response = requests.post(tally_url, data=tally_xml, headers=headers, timeout=10)

        if response.status_code == 200:
            frappe.msgprint("Student sent to Tally successfully")
            return {"status": "success", "message": "Student sent to Tally", "response": response.text}
        else:
            frappe.log_error(f"Tally Integration Failed: {response.text}", "Tally Integration Error")
            return {"status": "error", "message": "Failed to send data to Tally", "response": response.text}

    except Exception as e:
        frappe.log_error(f"Tally Integration Error: {str(e)}", "Tally Integration Error")
        return {"status": "error", "message": str(e)}
    

def convert_to_tally_ledger_xml(students):
    root = ET.Element("ENVELOPE")
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")

    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "All Masters"

    static_variables = ET.SubElement(request_desc, "STATICVARIABLES")
    ET.SubElement(static_variables, "SVCURRENTCOMPANY").text = frappe.db.get_single_value('Global Defaults', 'default_company')

    request_data = ET.SubElement(import_data, "REQUESTDATA")
    tally_message = ET.SubElement(request_data, "TALLYMESSAGE")

    for student in students:
        ledger = ET.SubElement(tally_message, "LEDGER", {"Action": "Create"})
        ET.SubElement(ledger, "NAME").text = f"{student['first_name']} {student['last_name']}-{student['name']}"
        ET.SubElement(ledger, "PARENT").text = "Sundry Debtors"

        mailing_details = ET.SubElement(ledger, "LEDMAILINGDETAILS.LIST")
        address_list = ET.SubElement(mailing_details, "ADDRESS.LIST", {"TYPE": "String"})
        ET.SubElement(address_list, "ADDRESS").text = student.get("address_line_1", "")
        ET.SubElement(address_list, "ADDRESS").text = student.get("address_line_2", "")

        ET.SubElement(mailing_details, "APPLICABLEFROM").text = "20240401"
        ET.SubElement(mailing_details, "PINCODE").text = student.get("pincode", "")
        ET.SubElement(mailing_details, "MAILINGNAME").text = f"{student['first_name']} {student['last_name']}"
        ET.SubElement(mailing_details, "STATE").text = student.get("state", "")
        ET.SubElement(mailing_details, "COUNTRY").text = student.get("country", "")

    return ET.tostring(root, encoding="utf-8").decode("utf-8")

@frappe.whitelist()
def send_fee_category_to_tally(doc, method):  
    try:
        fee_category = doc.as_dict()  
        categories = [fee_category]  

        tally_xml = convert_to_tally_fee_category_xml(categories)

        headers = {"Content-Type": "text/xml"}
        response = requests.post(tally_url, data=tally_xml, headers=headers, timeout=10)

        if response.status_code == 200:
            frappe.msgprint("Fee Category sent to Tally successfully")
            return {"status": "success", "message": "Fee Category sent to Tally", "response": response.text}
        else:
            frappe.log_error(f"Tally Integration Failed: {response.text}", "Tally Integration Error")
            return {"status": "error", "message": "Failed to send data to Tally", "response": response.text}

    except Exception as e:
        frappe.log_error(f"Tally Integration Error: {str(e)}", "Tally Integration Error")
        return {"status": "error", "message": str(e)}
    
def convert_to_tally_fee_category_xml(categories):
    root = ET.Element("ENVELOPE")
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")

    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "All Masters"

    static_variables = ET.SubElement(request_desc, "STATICVARIABLES")
    ET.SubElement(static_variables, "SVCURRENTCOMPANY").text = frappe.db.get_single_value('Global Defaults', 'default_company')

    request_data = ET.SubElement(import_data, "REQUESTDATA")
    tally_message = ET.SubElement(request_data, "TALLYMESSAGE", {"xmlns:UDF": "TallyUDF"})

    for category in categories:
        ledger = ET.SubElement(tally_message, "LEDGER", {"NAME": category["name"], "ACTION": "Create"})
        ET.SubElement(ledger, "NAME").text = category["name"]
        ET.SubElement(ledger, "PARENT").text = "Indirect Incomes"  

    return ET.tostring(root, encoding="utf-8").decode("utf-8")

@frappe.whitelist()
def send_fees_to_tally(doc, method):
    """Sends Fees data from ERPNext to Tally as a Journal Entry."""
    try:
        fees = doc.as_dict()
        student = frappe.get_doc("Student", fees.get("student"))
        ledger_name = f"{student.first_name} {student.last_name} - {student.name}"

        tally_xml = convert_to_tally_fees_xml(fees, ledger_name)

        frappe.log_error(f"Generated XML:\n{tally_xml}", "Debug Tally XML")
        frappe.msgprint(f"Generated XML:\n{tally_xml}")

        headers = {"Content-Type": "text/xml"}
        response = requests.post(tally_url, data=tally_xml, headers=headers, timeout=10)

        frappe.log_error(f"Tally Response:\n{response.text}", "Debug Tally Response")
        frappe.msgprint(f"Tally Response:\n{response.text}")

        if response.status_code == 200 and "<CREATED>1</CREATED>" in response.text:
            return {"status": "success", "message": "Fees data sent to Tally", "response": response.text}
        else:
            return {"status": "error", "message": "Tally did not create Journal Entry", "response": response.text}

    except Exception as e:
        frappe.log_error(f"Tally Integration Error: {str(e)}", "Tally Integration Error")
        return {"status": "error", "message": str(e)}

def convert_to_tally_fees_xml(fees, ledger_name):
    """Converts Fees data to Tally XML format with additional fields."""
    root = ET.Element("ENVELOPE")

    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")

    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"

    static_variables = ET.SubElement(request_desc, "STATICVARIABLES")
    ET.SubElement(static_variables, "SVCURRENTCOMPANY").text = fees.get("company", frappe.db.get_single_value('Global Defaults', 'default_company'))

    request_data = ET.SubElement(import_data, "REQUESTDATA")
    tally_message = ET.SubElement(request_data, "TALLYMESSAGE")

    voucher = ET.SubElement(tally_message, "VOUCHER", {"VCHTYPE": "Journal", "ACTION": "Create"})
    ET.SubElement(voucher, "DATE").text = fees.get("posting_date").replace("-", "") 
    ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Journal"
    ET.SubElement(voucher, "PARTYLEDGERNAME").text = ledger_name
    ET.SubElement(voucher, "VOUCHERNUMBER").text = fees.get("name")
    ET.SubElement(voucher, "PERSISTEDVIEW").text = "Accounting Voucher View"
    ET.SubElement(voucher, "REFERENCE").text = fees.get("name")
    ET.SubElement(voucher, "NARRATION").text = f"Fee {fees.name} being receivable by student {fees.student_name} for {fees.program} for year  {fees.academic_year}, {fees.academic_term},  of total amount {fees.grand_total}."
     
    total_credit = 0

    debit_amount = float(fees.get('grand_total', 0))
    if debit_amount > 0:
        debit_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(debit_entry, "LEDGERNAME").text = ledger_name
        ET.SubElement(debit_entry, "ISDEEMEDPOSITIVE").text = "Yes"  
        ET.SubElement(debit_entry, "AMOUNT").text = f"-{debit_amount:.2f}"
        ET.SubElement(debit_entry, "ISPARTYLEDGER").text = "Yes"

    if "components" in fees and fees["components"]:
        for component in fees["components"]:
            fee_category = component.get('fees_category')
            amount = float(component.get('amount', 0))

            if not fee_category or amount <= 0:
                continue  
            total_credit += amount  

            credit_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
            ET.SubElement(credit_entry, "LEDGERNAME").text = fee_category
            ET.SubElement(credit_entry, "ISDEEMEDPOSITIVE").text = "No" 
            ET.SubElement(credit_entry, "AMOUNT").text = f"{amount:.2f}"
            ET.SubElement(credit_entry, "ISPARTYLEDGER").text = "No"

    frappe.log_error(f"Total Debit: {debit_amount:.2f}, Total Credit: {total_credit:.2f}", "Debug Tally Amounts")
    frappe.msgprint(f"Total Debit: {debit_amount:.2f}, Total Credit: {total_credit:.2f}")

    return ET.tostring(root, encoding="utf-8").decode("utf-8")

@frappe.whitelist()
def send_receipt_to_tally(doc, method):
    """Sends Payment Entry data from ERPNext to Tally as a Receipt Voucher."""
    try:
        payment = doc.as_dict()

        account_paid_to = frappe.get_value("Account", payment.get("paid_to"))
        if not account_paid_to:
            frappe.throw("Account Paid To (Bank/Cash Ledger) is missing in ERPNext.")

        student = frappe.get_value("Student", {"student_name": payment.get("party_name")}, ["name", "first_name", "last_name"])
        if not student:
            frappe.throw(f"Student '{payment.get('party_name')}' not found.")

        student_id, first_name, last_name = student
        ledger_name = f"{first_name} {last_name}-{student_id}" 

        tally_xml = convert_to_tally_receipt_xml(payment, ledger_name, account_paid_to)

        frappe.log_error(f"Generated XML:\n{tally_xml}", "Debug Tally XML")
        frappe.msgprint(f"Generated XML:\n{tally_xml}")

        headers = {"Content-Type": "text/xml"}
        response = requests.post(tally_url, data=tally_xml, headers=headers, timeout=10)

        frappe.log_error(f"Tally Response:\n{response.text}", "Debug Tally Response")
        frappe.msgprint(f"Tally Response:\n{response.text}")

        frappe.msgprint(f"Paid To Account: {account_paid_to}")

        if response.status_code == 200 and "<CREATED>1</CREATED>" in response.text:
            return {"status": "success", "message": "Receipt sent to Tally", "response": response.text}
        else:
            return {"status": "error", "message": "Tally did not create Receipt Entry", "response": response.text}

    except Exception as e:
        frappe.log_error(f"Tally Integration Error: {str(e)}", "Tally Integration Error")
        return {"status": "error", "message": str(e)}

def convert_to_tally_receipt_xml(payment, ledger_name, account_paid_to):
    """Converts Payment Entry data to Tally XML format as a Receipt Voucher."""
    root = ET.Element("ENVELOPE")

    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "Import Data"

    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")

    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "Vouchers"

    static_variables = ET.SubElement(request_desc, "STATICVARIABLES")
    ET.SubElement(static_variables, "SVCURRENTCOMPANY").text = payment.get("company", frappe.db.get_single_value('Global Defaults', 'default_company'))

    request_data = ET.SubElement(import_data, "REQUESTDATA")
    tally_message = ET.SubElement(request_data, "TALLYMESSAGE")

    voucher = ET.SubElement(tally_message, "VOUCHER", {"VCHTYPE": "Receipt", "ACTION": "Create"})
    ET.SubElement(voucher, "DATE").text = payment.get("posting_date").replace("-", "") 
    ET.SubElement(voucher, "VOUCHERTYPENAME").text = "Receipt"
    ET.SubElement(voucher, "VOUCHERNUMBER").text = payment.get("name")
    ET.SubElement(voucher, "PERSISTEDVIEW").text = "Accounting Voucher View"
    ET.SubElement(voucher, "REFERENCE").text = payment.get("name")
    ET.SubElement(voucher, "REFERENCEDATE").text = payment.get("reference_date").replace("-", "") 
    ET.SubElement(voucher, "NARRATION").text = payment.get("remarks")

    received_amount = float(payment.get('paid_amount', 0))

    ET.SubElement(voucher, "ACCOUNT").text = account_paid_to  

    if received_amount > 0:
        party_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(party_entry, "LEDGERNAME").text = ledger_name
        ET.SubElement(party_entry, "ISDEEMEDPOSITIVE").text = "No"  
        ET.SubElement(party_entry, "AMOUNT").text = f"{abs(received_amount):.2f}"
        ET.SubElement(party_entry, "ISPARTYLEDGER").text = "Yes"

    if received_amount > 0:
        bank_entry = ET.SubElement(voucher, "ALLLEDGERENTRIES.LIST")
        ET.SubElement(bank_entry, "LEDGERNAME").text = account_paid_to  
        ET.SubElement(bank_entry, "ISDEEMEDPOSITIVE").text = "Yes" 
        ET.SubElement(bank_entry, "AMOUNT").text = f"-{abs(received_amount):.2f}"
        ET.SubElement(bank_entry, "ISPARTYLEDGER").text = "No"

    return ET.tostring(root, encoding="utf-8").decode("utf-8")
