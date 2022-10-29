import django_tables2 as tables

from statuspage.tables import StatusPageTable, columns
from .models import Metric


class MetricTable(StatusPageTable):
    title = tables.Column(
        linkify=True,
    )
    status = columns.ChoiceFieldColumn()
    visibility = columns.BooleanColumn()

    class Meta(StatusPageTable.Meta):
        model = Metric
        fields = ('pk', 'id', 'title', 'status', 'visibility', 'expand', 'created', 'last_updated')
        default_columns = ('id', 'title', 'status', 'visibility', 'expand')
