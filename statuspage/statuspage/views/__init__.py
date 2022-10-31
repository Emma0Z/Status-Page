import platform
import sys

from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.csrf import requires_csrf_token
from django.views.defaults import ERROR_500_TEMPLATE_NAME
from django.template import loader
from django.template.exceptions import TemplateDoesNotExist
from django.http import HttpResponseServerError

from components.models import ComponentGroup
from incidents.models import Incident
from incidents.choices import IncidentStatusChoices
from maintenances.models import Maintenance
from maintenances.choices import MaintenanceStatusChoices
from statuspage.views.generic import BaseView
from subscribers.models import Subscriber


class HomeView(BaseView):
    template_name = 'home.html'

    def get(self, request):
        component_groups = ComponentGroup.objects.filter(
            visibility=True,
        )
        open_incidents = Incident.objects.filter(
            ~Q(status=IncidentStatusChoices.RESOLVED),
            visibility=True,
        )
        resolved_incidents = Incident.objects.filter(
            status=IncidentStatusChoices.RESOLVED,
            visibility=True,
        )

        return render(request, self.template_name, {
            'component_groups': component_groups,
            'open_incidents': open_incidents,
            'resolved_incidents': resolved_incidents,
        })


class DashboardHomeView(BaseView):
    template_name = 'dashboard/home.html'

    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("login")

        open_incidents = Incident.objects.filter(
            ~Q(status=IncidentStatusChoices.RESOLVED)
        )
        open_maintenances = Maintenance.objects.filter(
            ~Q(status=MaintenanceStatusChoices.COMPLETED)
        )
        upcoming_maintenances = Maintenance.objects.filter(
            ~Q(status=MaintenanceStatusChoices.COMPLETED),
            scheduled_at__gte=timezone.now(),
        )

        return render(request, self.template_name, {
            'open_incidents': len(open_incidents),
            'open_maintenances': len(open_maintenances),
            'upcoming_maintenances': len(upcoming_maintenances),
        })


class SubscriberVerifyView(BaseView):
    def get(self, request, **kwargs):
        subscriber = Subscriber.get_by_management_key(**kwargs)

        if not subscriber:
            messages.error(request, 'This Subscriber has not been found.')
            return redirect('home')

        if subscriber.email_verified_at:
            messages.error(request, 'This E-Mail is already verified.')
            return redirect('subscriber_manage', **kwargs)

        subscriber.email_verified_at = timezone.now()
        subscriber.save()
        messages.success(request, 'This E-Mail has been verified.')
        return redirect('subscriber_manage', **kwargs)


class SubscriberManageView(BaseView):
    template_name = 'home/subscribers/manage.html'

    def get(self, request, **kwargs):
        subscriber = Subscriber.get_by_management_key(**kwargs)

        if not subscriber:
            messages.error(request, 'This Subscriber has not been found.')
            return redirect('home')

        if not subscriber.email_verified_at:
            messages.error(request, 'This E-Mail is not verified.')
            return redirect('home')

        return render(request, self.template_name)


class SubscriberUnsubscribeView(BaseView):
    template_name = 'home/subscribers/unsubscribe.html'

    def get(self, request, **kwargs):
        subscriber = Subscriber.get_by_management_key(**kwargs)

        if not subscriber:
            messages.error(request, 'This Subscriber has not been found.')
            return redirect('home')

        if not subscriber.email_verified_at:
            messages.error(request, 'This E-Mail is not verified.')
            return redirect('home')

        return render(request, self.template_name)

    def post(self, request, **kwargs):
        subscriber = Subscriber.get_by_management_key(**kwargs)

        if not subscriber:
            messages.error(request, 'This Subscriber has not been found.')
            return redirect('home')

        if not subscriber.email_verified_at:
            messages.error(request, 'This E-Mail is not verified.')
            return redirect('home')

        subscriber.delete()
        messages.success(request, 'Successfully unsubscribed.')
        return redirect('home')


@requires_csrf_token
def server_error(request, template_name=ERROR_500_TEMPLATE_NAME):
    """
    Custom 500 handler to provide additional context when rendering 500.html.
    """
    try:
        template = loader.get_template(template_name)
    except TemplateDoesNotExist:
        return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
    type_, error, traceback = sys.exc_info()

    return HttpResponseServerError(template.render({
        'error': error,
        'exception': str(type_),
        'statuspage_version': settings.VERSION,
        'python_version': platform.python_version(),
    }))
