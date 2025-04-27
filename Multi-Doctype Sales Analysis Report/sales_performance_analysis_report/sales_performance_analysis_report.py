import frappe

def execute(filters=None):
    columns = [
        {"fieldname": "sales_person", "label": "Sales Person", "fieldtype": "Data", "width": 150},
        {"fieldname": "item_group", "label": "Item Group", "fieldtype": "Data", "width": 150},
        {"fieldname": "total_revenue", "label": "Total Revenue", "fieldtype": "Currency", "width": 150},
        {"fieldname": "order_fulfillment_rate", "label": "Order Fulfillment Rate (%)", "fieldtype": "Percent", "width": 180},
        {"fieldname": "payment_collection_efficiency", "label": "Payment Collection Efficiency (%)", "fieldtype": "Percent", "width": 200},
    ]
    
    data = get_data(filters)

    return columns, data

def get_data(filters):
    conditions = ""
    if filters.get("from_date") and filters.get("to_date"):
        conditions += f" AND so.transaction_date BETWEEN '{filters['from_date']}' AND '{filters['to_date']}'"
    if filters.get("item_group"):
        conditions += f" AND i.item_group = '{filters['item_group']}'"

    sales_data = frappe.db.sql(f"""
        SELECT
            sp.sales_person,
            i.item_group,
            SUM(si_item.net_amount) AS total_revenue,
            CASE WHEN COUNT(DISTINCT so.name) > 0 
                THEN (COUNT(DISTINCT dn.name) / COUNT(DISTINCT so.name)) * 100
                ELSE 0
            END AS order_fulfillment_rate,
            CASE WHEN SUM(si_item.net_amount) > 0 
                THEN (SUM(pe.allocated_amount) / SUM(si_item.net_amount)) * 100
                ELSE 0
            END AS payment_collection_efficiency
        FROM
            `tabSales Order` so
        LEFT JOIN
            `tabSales Invoice Item` si_item ON si_item.sales_order = so.name
        LEFT JOIN
            `tabSales Invoice` si ON si.name = si_item.parent
        LEFT JOIN
            `tabDelivery Note Item` dn_item ON dn_item.against_sales_order = so.name
        LEFT JOIN
            `tabDelivery Note` dn ON dn.name = dn_item.parent
        LEFT JOIN
            `tabSales Team` sp ON sp.parent = so.name
        LEFT JOIN
            `tabItem` i ON i.name = si_item.item_code
        LEFT JOIN
            `tabPayment Entry Reference` pe ON pe.reference_name = si.name
        WHERE
            so.docstatus = 1
            {conditions}
        GROUP BY
            sp.sales_person, i.item_group
    """, as_dict=1)

    return sales_data