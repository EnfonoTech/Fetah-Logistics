frappe.ui.form.on('Sales Order', {
    onload: async function (frm) {
        if (frm.is_new() && frm.doc.custom_job_record) {
            frappe.db.get_value("Job Record", frm.doc.custom_job_record, 'po_no')
              .then(r=>{
                if (r.message && r.message.po_no) {
                    frm.set_value('po_no', r.message.po_no);
                }
              })
            try {
                const r = await frappe.call({
                    method: 'fateh_logistics.api.get_remaining_items_from_job',
                    args: {
                        job_record_id: frm.doc.custom_job_record,
                        target_doctype: 'Sales Order'
                    }
                });

                if (r.message && Array.isArray(r.message)) {
                    frm.clear_table('items');
                    r.message.forEach(row => {
                        frm.add_child('items', {
                            item_code: row.item_code,
                            item_name: row.item_name,
                            // description: row.description,
                            qty: row.qty,
                            uom: row.uom,
                            rate: row.rate,
                            amount: row.amount
                            // schedule_date: row.schedule_date,
                            // warehouse: row.warehouse
                        });
                    });
                    frm.refresh_field('items');
                }
            } catch (err) {
                frappe.msgprint(__('Failed to load remaining Job Record items.'));
                console.error(err);
            }
        }
    }
});





