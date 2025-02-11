import frappe
import requests
import xml.etree.ElementTree as ET

TALLY_URL = "http://localhost:9000"  # Change this for production

@frappe.whitelist()
def send_students_to_tally():
    try:
        # Fetch all students from ERPNext
        students = frappe.get_all("Student", fields=["name", "student_name", "email", "phone", "address", "opening_balance"])

        if not students:
            return {"status": "error", "message": "No students found"}

        # Convert students data to Tally XML
        tally_xml = convert_to_tally_ledger_xml(students)

        # Send XML to TallyPrime
        headers = {"Content-Type": "text/xml"}
        response = requests.post(TALLY_URL, data=tally_xml, headers=headers, timeout=10)

        # Check response
        if response.status_code == 200:
            return {"status": "success", "message": "Students sent to Tally", "response": response.text}
        else:
            return {"status": "error", "message": "Failed to send data to Tally", "response": response.text}

    except Exception as e:
        return {"status": "error", "message": str(e)}

def convert_to_tally_ledger_xml(students):
    """
    Converts ERPNext student data to Tally XML Ledger format.
    """
    root = ET.Element("ENVELOPE")

    # Header
    header = ET.SubElement(root, "HEADER")
    ET.SubElement(header, "TALLYREQUEST").text = "IMPORT"
    
    # Body
    body = ET.SubElement(root, "BODY")
    import_data = ET.SubElement(body, "IMPORTDATA")
    
    # Request Description
    request_desc = ET.SubElement(import_data, "REQUESTDESC")
    ET.SubElement(request_desc, "REPORTNAME").text = "All Masters"

    request_data = ET.SubElement(import_data, "REQUESTDATA")
    tally_message = ET.SubElement(request_data, "TALLYMESSAGE")

    # Convert JSON Student Data to Ledger XML
    for student in students:
        ledger = ET.SubElement(tally_message, "LEDGER", {"Action": "Create"})
        ET.SubElement(ledger, "NAME").text = student["student_name"]
        ET.SubElement(ledger, "PARENT").text = "Sundry Debtors"  # Change as per your Tally group
        ET.SubElement(ledger, "MAILINGNAME").text = student["student_name"]
        ET.SubElement(ledger, "ADDRESS").text = student.get("address", "")
        ET.SubElement(ledger, "EMAIL").text = student.get("email", "")
        ET.SubElement(ledger, "PHONE").text = student.get("phone", "")
        ET.SubElement(ledger, "OPENINGBALANCE").text = student.get("opening_balance", "0")

    # Convert XML to string
    return ET.tostring(root, encoding="utf-8").decode("utf-8")
