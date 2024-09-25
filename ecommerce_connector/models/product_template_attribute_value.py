# Copyright 2022 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class ProductTemplateAttributeValue(models.Model):
    _inherit = "product.template.attribute.value"

    def _get_combination_name(self):
        values = super()._get_combination_name()
        if not values and self.attribute_line_id.product_template_value_ids:
            ptavs = self._without_no_variant_attributes().with_prefetch(
                self._prefetch_ids
            )
            values = ", ".join([ptav.name for ptav in ptavs])
        return values
