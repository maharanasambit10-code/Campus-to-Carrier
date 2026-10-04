from django import template

register = template.Library()


@register.simple_tag
def get_form_fields(form, field_names):
    return [form[name] for name in field_names.split(',') if name in form.fields]
