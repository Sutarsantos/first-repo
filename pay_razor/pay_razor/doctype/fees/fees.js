// Copyright (c) 2025, santoshsutar3130@gmail.com and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Fees", {
// 	refresh(frm) {

// 	},
// });
frappe.ui.form.on('Fees', {
    refresh: function(frm) {
        // Add a custom button for "Pay Now" on the form
        frm.add_custom_button(__('Pay Now'), function() {
            // Validate required fields before making the API call
            if (!frm.doc.full_name || !frm.doc.email_id || !frm.doc.company_name || !frm.doc.amount) {
                frappe.msgprint(__('Please fill all mandatory fields: Full Name, Email, Company, and Amount.'));
                return;
            }

            // Prepare the data to send to the API
            const paymentData = {
                full_name: frm.doc.full_name,
                email: frm.doc.email_id,
                company: frm.doc.company_name,
                amount: frm.doc.amount,
                workshop: frm.doc.workshop || 0,
                conference: frm.doc.conference || 0
            };

            // Call the custom server-side API to generate Razorpay URL
            frappe.call({
                method: 'pay_razor.pay_razor.doctype.fees.fees.make_payment', // Ensure this path matches your server-side method
                args: paymentData,
                callback: function(response) {
                    if (response && response.message) {
                        // Redirect to Razorpay checkout URL
                        window.location.href = response.message;
                    } else {
                        frappe.msgprint(__('Failed to generate payment URL. Please try again.'));
                    }
                },
                error: function(err) {
                    frappe.msgprint(__('An error occurred while processing the payment. Please try again.'));
                    console.error(err);
                }
            });
        });
    }
});
