import frappe
from frappe.model.document import Document
from razorpay_integration.api import get_razorpay_checkout_url

class Fees(Document):
    pass

@frappe.whitelist(allow_guest=True)
def make_payment(full_name, email_id, company_name, amount, workshop=None, conference=None):
    try:
        # Create a Fees document
        fees = frappe.get_doc({
            'doctype': 'Fees',
            'full_name': full_name,
            'email_id': email_id,
            'company_name': company_name,
            'workshop': workshop,
            'conference': conference,
            'amount': amount
        }).insert()

        # Commit the transaction to save the document in the database
        frappe.db.commit()

        # Get Razorpay checkout URL
        url = get_razorpay_checkout_url(**{
            'amount': int(float(amount) * 100),  # Convert amount to paise for Razorpay
            'title': 'ERPNext Conference Tickets',
            'description': '{0} passes for conference, {1} passes for workshop'.format(
                int(conference or 0), int(workshop or 0)),
            'payer_name': full_name,
            'payer_email': email_id,
            'doctype': fees.doctype,
            'name': fees.name,
            'order_id': fees.name  # Using Fees name as the order ID
        })

        # Return the Razorpay checkout URL
        return {'message': url['url'] if isinstance(url, dict) else url}

    except Exception as e:
        # Log the error and throw a user-friendly message
        frappe.log_error(frappe.get_traceback(), "Payment Processing Error")
        frappe.throw(_("An error occurred while processing the payment. Please try again later."))
