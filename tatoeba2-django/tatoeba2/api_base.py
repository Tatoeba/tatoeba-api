from tastypie.resources import Resource, DeclarativeMetaclass, ResourceOptions
from tastypie import fields
from tastypie.paginator import Paginator
from tastypie.exceptions import InvalidFilterError, InvalidSortError
from haystack.query import SearchQuerySet, AutoQuery, SQ
from .utils import stemmer
from django.db import connection


class UCharField(fields.ApiField):
    dehydrated_type = 'string'
    help_text = 'Unicode string data. Ex: "Hello World"'

    def convert(self, value):
        if value is None:
            return None

        return value.decode('utf-8', 'ignore')


class IDPaginator(Paginator):

    def get_slice(self, limit, offset):
        if limit == 0:
            return list(self.objects.order_by('id').filter(id__gte=offset))

        return list(self.objects.order_by('id').filter(id__gte=offset)[:limit])

    def get_count(self):
        query = self.objects.query

        query, params = query.sql_with_params()
        query = 'EXPLAIN %s' % query

        cursor = connection.cursor()
        cursor.execute(query, params)
        count = cursor.fetchone()[-2]

        return count

    def get_next(self, limit, offset):
        return self._generate_uri(limit, offset)

    def page(self):
        limit = self.get_limit()
        offset = self.get_offset()
        count = self.get_count()
        objects = self.get_slice(limit, offset)
        next_offset = objects[-1].id
        meta = {
            'offset': offset,
            'limit': limit,
            'total_count': count,
        }

        if limit:
            meta['next'] = self.get_next(limit, next_offset)

        return {
            self.collection_name: objects,
            'meta': meta,
        }


LOOKUP_SEP = '__'

class SearchOptions(ResourceOptions):
    resource_name = 'search'
    object_class = SearchQuerySet
    object_query = SQ
    detail_uri_name = 'django_id'
    index = None
    model = None
    autoquery_fields = []
    stem_fields = []
    max_limit = 100


class SearchDeclarativeMetaclass(DeclarativeMetaclass):
    def __new__(cls, name, bases, attrs):
        new_class = super(SearchDeclarativeMetaclass, cls).__new__(cls, name, bases, attrs)
        opts = getattr(new_class, 'Meta', None)
        new_class._meta = SearchOptions(opts)
        include_fields = getattr(new_class._meta, 'fields', [])
        excludes = getattr(new_class._meta, 'excludes', [])
        excludes.append('text')
        field_names = new_class.base_fields.keys()

        if getattr(new_class._meta, 'index', None):
            new_class._meta.model = new_class.Meta.index.get_model()

        for field_name in field_names:
            if field_name == 'resource_uri':
                continue
            if field_name in new_class.declared_fields:
                continue
            if len(include_fields) and not field_name in include_fields:
                del(new_class.base_fields[field_name])
            if len(excludes) and field_name in excludes:
                del(new_class.base_fields[field_name])

        new_class.base_fields.update(new_class.get_fields(include_fields, excludes))

        if getattr(new_class._meta, 'include_absolute_url', True):
            if not 'absolute_url' in new_class.base_fields:
                new_class.base_fields['absolute_url'] = fields.CharField(
                    attribute='get_absolute_url', readonly=True)
        elif 'absolute_url' in new_class.base_fields and not 'absolute_url' in attrs:
            del(new_class.base_fields['absolute_url'])

        return new_class


class BaseSearchResource(Resource):
    __metaclass__ = SearchDeclarativeMetaclass

    django_id = fields.IntegerField(attribute='django_id')

    @classmethod
    def api_field_from_haystack_field(cls, f, default=fields.CharField):
        result = default

        internal_type = f.__class__.__name__

        if internal_type in ('DateTimeField', 'DateField'):
            result = fields.DateTimeField
        elif internal_type in ('BooleanField',):
            result = fields.BooleanField
        elif internal_type in ('FloatField',):
            result = fields.FloatField
        elif internal_type in ('DecimalField',):
            result = fields.DecimalField
        elif internal_type in ('IntegerField',):
            result = fields.IntegerField

        return result

    @classmethod
    def get_fields(cls, fields=None, excludes=None):
        final_fields = {}
        fields = fields or []
        excludes = excludes or []

        if not cls._meta.index:
            return final_fields

        for f, f_class in cls._meta.index.fields.items():

            if f in cls.base_fields:
                continue

            if fields and f not in fields:
                continue

            if excludes and f in excludes:
                continue

            api_field_class = cls.api_field_from_haystack_field(f_class)

            final_fields[f] = api_field_class(**{'attribute': f})
            final_fields[f].instance_name = f

        return final_fields

    def detail_uri_kwargs(self, bundle_or_obj):
        kwargs = {}
        if isinstance(bundle_or_obj, SearchQuerySet):
            kwargs[self._meta.detail_uri_name] = getattr(bundle_or_obj, self._meta.detail_uri_name)
        else:
            kwargs[self._meta.detail_uri_name] = getattr(bundle_or_obj.obj, self._meta.detail_uri_name)
        return kwargs

    def check_filtering(self, field_name, filter_type='contains'):
        if not field_name in self._meta.filtering:
            raise InvalidFilterError("The '%s' field does not allow filtering." % field_name)

        if not filter_type in self._meta.filtering[field_name]:
            raise InvalidFilterError("'%s' is not an allowed filter on the '%s' field." % (filter_type, field_name))

        return True

    def filter_value_to_python(self, filter_type, value):
        if value in ['true', 'True', True]:
            value = True
        elif value in ['false', 'False', False]:
            value = False
        elif value in ('none', 'None', None):
            value = None

        if filter_type in ('in', 'range') and len(value):
            value = value.replace('[', '').replace(']', '')
            value = value.split(',')

        return value

    def build_filters(self, filters=None, stem_lang=''):
        if filters is None:
            filters = {}

        applicable_filters = {}
        for filter_expr, value in filters.items():
            lookup_bits = filter_expr.split(LOOKUP_SEP)
            field_name = lookup_bits.pop(0)
            filter_type = lookup_bits.pop() if lookup_bits else 'contains'
            filter_expr = LOOKUP_SEP.join([field_name, filter_type])
            filter_value = self.filter_value_to_python(filter_type, value)

            if field_name in self._meta.stem_fields and stem_lang:
                filter_value = stemmer.stem(filter_value, stem_lang)

            if field_name in self._meta.autoquery_fields:
                filter_value = AutoQuery(filter_value)

            if self.check_filtering(field_name, filter_type):
                applicable_filters[filter_expr] = filter_value

        return applicable_filters

    def apply_filters(self, request, filters=None, join_op='and'):
        SQ = self._meta.object_query
        query = SQ()

        if join_op == 'and':
            for fltr, val in filters.items():
                query = query & SQ(**{fltr: val})

        if join_op == 'or':
            for fltr, val in filters.items():
                query = query | SQ(**{fltr: val})

        if join_op == 'not':
            for fltr, val in filters.items():
                query = query & ~SQ(**{fltr: val})

        return self.get_object_list(request).filter(query)

    def apply_sort(self, obj_list, sort_expr):
        field_name = sort_expr[1:] if sort_expr.startswith('-') else sort_expr

        if not field_name in self.fields:
            raise InvalidSortError("No matching '%s' field for ordering on." % field_name)

        if not field_name in self._meta.ordering:
            InvalidSortError("The '%s' field does not allow ordering." % field_name)

        return obj_list.order_by(sort_expr)

    def get_object_list(self, request):
        return self._meta.object_class().models(self._meta.model)

    def obj_get_list(self, request=None, **kwargs):
        filters = {}
        request = kwargs['bundle'].request

        if hasattr(request, 'GET'):
            filters = request.GET.copy()

        and_filters = {}
        or_filters = {}
        not_filters = {}

        sort_expr = filters.get('order_by')
        if sort_expr: del filters['order_by']

        del filters['format']
        if 'offset' in filters.keys(): del filters['offset']
        if 'limit' in filters.keys(): del filters['limit']

        for fltr, val in filters.items():

            if fltr[0] == '|':
                or_filters[fltr[1:]] = val
            elif fltr[0] == '~':
                not_filters[fltr[1:]] = val
            else:
                and_filters[fltr] = val

            del filters[fltr]

        result = self.get_object_list(request)

        if and_filters:
            stem_lang = and_filters.get('lang') or ''
            applicable_filters = self.build_filters(and_filters, stem_lang)
            result = self.apply_filters(request, applicable_filters)

        if or_filters:
            applicable_filters = self.build_filters(or_filters)
            result = result | self.apply_filters(request, applicable_filters, 'or')

        if not_filters:
            applicable_filters = self.build_filters(not_filters)
            result = result & self.apply_filters(request, applicable_filters, 'not')

        if sort_expr:
            result = self.apply_sort(result, sort_expr)

        return result

    def obj_get(self, request=None, **kwargs):
        pk_fld = self._meta.detail_uri_name
        pk = kwargs.get(pk_fld)
        sqs = self.get_object_list(request)

        if pk:
            sqs = sqs.filter(**{pk_fld: pk})

            if sqs:
                return sqs[0]
            else:
                return sqs
