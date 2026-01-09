import logging

from home.services.cross_sell import CrossSellHtmlService
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.request import Request
from rest_framework.response import Response

logger = logging.getLogger(__file__)


@api_view(("GET",))
def cross_sell_widget(request: Request) -> Response:
    content_type = "application/javascript"
    shop_url = request.GET.get("shop")
    checkout_token = request.GET.get("checkout_token")
    customer_id = request.GET.get("checkout_customer_id")
    customer_email = request.GET.get("checkout_customer_email")
    customer_first_name = request.GET.get("checkout_shipping_address_first_name")
    customer_last_name = request.GET.get("checkout_shipping_address_last_name")
    cms_variant_ids = list(filter(lambda x: x, request.GET.get("variant_ids", "").split(",")))
    cms_product_ids = list(filter(lambda x: x, request.GET.get("product_ids", "").split(",")))
    quantities = list(filter(lambda x: x, request.GET.get("quantities", "").split(",")))
    total_prices = list(filter(lambda x: x, request.GET.get("total_prices", "").split(",")))

    # generated_sales.delay(
    #     shop_url,
    #     checkout_token,
    #     customer_id,
    #     customer_email,
    #     customer_first_name,
    #     customer_last_name,
    #     cms_variant_ids,
    #     cms_product_ids,
    #     quantities,
    #     total_prices,
    # )

    context = CrossSellHtmlService.widget_context(request)
    return Response(context, status=status.HTTP_200_OK)


# @api_view(("GET",))
# def cross_sell_widget(request: Request) -> HttpResponse:
#     content_type = "application/javascript"
#     shop_url = request.GET.get("shop")
#     checkout_token = request.GET.get("checkout_token")
#     customer_id = request.GET.get("checkout_customer_id")
#     customer_email = request.GET.get("checkout_customer_email")
#     customer_first_name = request.GET.get("checkout_shipping_address_first_name")
#     customer_last_name = request.GET.get("checkout_shipping_address_last_name")
#     cms_variant_ids = list(filter(lambda x: x, request.GET.get("variant_ids", "").split(",")))
#     cms_product_ids = list(filter(lambda x: x, request.GET.get("product_ids", "").split(",")))
#     quantities = list(filter(lambda x: x, request.GET.get("quantities", "").split(",")))
#     total_prices = list(filter(lambda x: x, request.GET.get("total_prices", "").split(",")))

#     generated_sales.delay(
#         shop_url,
#         checkout_token,
#         customer_id,
#         customer_email,
#         customer_first_name,
#         customer_last_name,
#         cms_variant_ids,
#         cms_product_ids,
#         quantities,
#         total_prices,
#     )

#     context = CrossSellHtmlService.widget_context(request)
#     if not context:
#         return HttpResponse(b"", content_type=content_type)

#     template = Template(CROSSSELL_WIDGET_HTML_TEMPLATE)
#     widget_text = template.render(Context(asdict_with_properties(context)))
#     return HttpResponse(widget_text, content_type=content_type)
