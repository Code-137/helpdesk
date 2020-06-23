import base64
import logging

import werkzeug

import odoo.http as http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HelpdeskTicketController(http.Controller):
    @http.route("/ticket/close", type="http", auth="public")
    def support_ticket_close(self, **kw):
        """Close the support ticket"""
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        ticket = (
            http.request.env["helpdesk.ticket"]
            .sudo()
            .search([("unique_eid", "=", values["ticket_eid"])])
        )
        ticket.stage_id = int(values.get("stage_id"))

        return werkzeug.utils.redirect("/my/ticket/" + ticket.unique_eid)

    @http.route("/new/ticket", type="http", auth="public", website=True)
    def create_new_ticket(self, **kw):
        categories = http.request.env["helpdesk.ticket.category"].sudo().search(
            [("active", "=", True)]
        )
        email = name = ''
        if not request.env.user.has_group('base.group_public'):
            email = http.request.env.user.email
            name = http.request.env.user.name
        return http.request.render(
            "helpdesk_mgmt.portal_create_ticket",
            {"categories": categories, "email": email, "name": name},
        )

    @http.route("/submitted/ticket", type="http", auth="public", website=True, csrf=True)
    def submit_ticket(self, **kw):
        vals = {
            "partner_name": kw.get("name"),
            "company_id": http.request.env.user.company_id.id,
            "category_id": kw.get("category"),
            "partner_email": kw.get("email"),
            "description": kw.get("description"),
            "name": kw.get("subject"),
            "attachment_ids": False,
            "channel_id": request.env["helpdesk.ticket.channel"]
            .sudo()
            .search([("name", "=", "Web")], limit=1)
            .id,
            "partner_id": request.env["res.partner"]
            .sudo()
            .search([("email", "=", kw.get("email"))], limit=1)
            .id,
        }
        new_ticket = request.env["helpdesk.ticket"].sudo().create(vals)
        new_ticket.message_subscribe(partner_ids=request.env.user.partner_id.ids)
        if kw.get("attachment"):
            for c_file in request.httprequest.files.getlist("attachment"):
                data = c_file.read()
                if c_file.filename:
                    request.env["ir.attachment"].sudo().create(
                        {
                            "name": c_file.filename,
                            "datas": base64.b64encode(data),
                            "res_model": "helpdesk.ticket",
                            "res_id": new_ticket.id,
                        }
                    )
        if request.env.user.has_group('base.group_public'):
            return werkzeug.utils.redirect("/my/ticket/" + new_ticket.unique_eid)
        return werkzeug.utils.redirect("/my/tickets")
