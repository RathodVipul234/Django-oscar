from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from oscar.apps.order.models import Order
from oscar.core.loading import get_model, get_class
OscarThankYouView = get_class("checkout.views", "ThankYouView")

# Create your views here.
from django.template.loader import render_to_string
from django.http import HttpResponse
import weasyprint
from django.views import generic

from django.shortcuts import redirect, render


# from . import PAYMENT_METHOD_STRIPE, PAYMENT_EVENT_PURCHASE, STRIPE_EMAIL, STRIPE_TOKEN
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
# from .facade import Facade
import logging
from django.core.mail import send_mail
from oscar.apps.payment.models import Source
from oscar.apps.order.models import Order
# from . import gateway
from oscar.apps.checkout import views as oscar_views
# from paypal.payflow import facade
from django.contrib import messages
# from rest_framework.views import APIView
# from rest_framework.permissions import AllowAny
from django.shortcuts import render, redirect, reverse
# from rest_framework.status import HTTP_200_OK
from django.shortcuts import redirect
from oscar.apps.payment.models import SourceType
from oscar.apps.payment.forms import BankcardForm
# from .forms import *
from oscar.apps.checkout import exceptions
from django.urls import reverse, reverse_lazy
from oscar.core.loading import get_model, get_class
# from globalsettings.models import Paymentmethod
OscarPaymentMethodView = get_class("checkout.views", "PaymentMethodView")
OscarPaymentDetailsView = get_class("checkout.views", "PaymentDetailsView")
OscarShippingMethodView = get_class("checkout.views", "ShippingMethodView")
OscarShippingAddressView = get_class("checkout.views", "ShippingAddressView")
OscarCheckoutSessionMixin = get_class("checkout.views", "CheckoutSessionMixin")
OscarThankYouView = get_class("checkout.views", "ThankYouView")
from django.views.generic import FormView
from django.conf import settings
BillingAddress = get_model("order", "BillingAddress")
from django.views import generic
from oscar.core.loading import get_classes, get_model
from django.template.loader import get_template
from xhtml2pdf import pisa

from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template


import os

def link_callback(uri, rel):
    sUrl = settings.STATIC_URL      # Typically /static/
    sRoot = settings.STATIC_ROOT    
    mUrl = settings.MEDIA_URL       # Typically /static/media/
    mRoot = settings.MEDIA_ROOT     # Typically /home/userX/project_static/media/

    path = "oscar/css/styles.css"
    # print(uri,rel)
    # # convert URIs to absolute system paths
    # if uri.startswith(mUrl):
    # elif uri.startswith(sUrl):
    #     path = os.path.join(sRoot, uri.replace(sUrl, ""))
    # else:
    #     return uri  # handle absolute uri (ie: http://some.tld/foo.png)

    # # make sure that file exists
    # import time
    # time.sleep(3)
    # # import pdb;pdb.set_trace()
    # # if not os.path.isfile(path):
    # #     raise Exception(
    # #         'media URI must start with %s or %s' % (sUrl, mUrl)
    # #     )
    return path


def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = BytesIO()
    pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)
    # pdf = pisa.CreatePDF(html.encode('utf-8'), dest=result,encoding='utf-8', link_callback=link_callback)
    if not pdf.err:
        response = HttpResponse(result.getvalue(), content_type='application/pdf')
        filename = "Invoice.pdf"
        # content = "inline; filename='%s'" %(filename)
        content = "attachment; filename=%s" %(filename)
        response['Content-Disposition'] = content
        return response
    return None

class ThankYouView1(generic.DetailView):
    """
    Displays the 'thank you' page which summarises the order just submitted.
    """
    # template_name = 'oscar/checkout/thank_you.html'
    template_name = 'thank_you.html'
    context_object_name = 'order'

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object is None:
            return redirect(settings.OSCAR_HOMEPAGE)
        context = self.get_context_data(object=self.object)
        context['request'] = self.request
        html_string = render_to_string(self.template_name, context)
        pdf = weasyprint.HTML(string=html_string).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="invoice.pdf'    
        return response

        # import pdb;pdb.set_trace()
        # return self.render_to_response(context)
        # return render_to_pdf(self.template_name,context)
        # template = get_template(self.template_name)
        # #THIS DON'T WORK
        # import pdb;pdb.set_trace()
        # html = template.render(context)

        # html_string = render_to_string(self.template_name, context, request=self.request)
        # pdf = render_to_pdf(self.template_name, context)
        # if pdf:
        #     response = HttpResponse(pdf, content_type='application/pdf')
        #     filename = "Invoice_%s.pdf" %("12341231")
        #     content = "inline; filename='%s'" %(filename)
        #     download = request.GET.get("download")
        #     if download:
        #         content = "attachment; filename='%s'" %(filename)
        #     response['Content-Disposition'] = content
        #     return response
        # return HttpResponse("Not found")

    def get_object(self, queryset=None):
        # We allow superusers to force an order thank-you page for testing
        order = None
        if self.request.user.is_superuser:
            kwargs = {}
            if 'order_number' in self.request.GET:
                kwargs['number'] = self.request.GET['order_number']
            elif 'order_id' in self.request.GET:
                kwargs['id'] = self.request.GET['order_id']
            order = Order._default_manager.filter(**kwargs).first()

        if not order:
            if 'checkout_order_id' in self.request.session:
                order = Order._default_manager.filter(
                    pk=self.request.session['checkout_order_id']).first()
        return order

    def get_context_data(self, *args, **kwargs):
        ctx = super().get_context_data(*args, **kwargs)
        # Remember whether this view has been loaded.
        # Only send tracking information on the first load.
        key = 'order_{}_thankyou_viewed'.format(ctx['order'].pk)
        if not self.request.session.get(key, False):
            self.request.session[key] = True
            ctx['send_analytics_event'] = True
        else:
            ctx['send_analytics_event'] = False

        return ctx


def genrate_pdf_from_html(request):
    context = dict()
    context['name'] = "Hello world"
    html_string = render_to_string('invoice.html', context)
    pdf = weasyprint.HTML(string=html_string).write_pdf()
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf'    
    return response

