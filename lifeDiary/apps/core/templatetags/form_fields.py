from django import template

register = template.Library()


def _error_id(field) -> str:
    return f"{field.auto_id}_error"


@register.simple_tag
def form_field(field, css_class="form-control", invalid=False):
    """Render a bound field wired to its own error node.

    Screen readers need the error text linked to the input, not merely placed
    near it. Callers pair this with `shared/_field_errors.html`, or with their
    own node carrying the same id.

    `invalid` forces the error state for messages that belong to a field but
    live on the form, such as an authentication failure.
    """
    attrs = {}
    classes = [field.field.widget.attrs.get("class", ""), css_class]

    if field.errors or invalid:
        attrs["aria-invalid"] = "true"
        attrs["aria-describedby"] = _error_id(field)
        classes.append("is-invalid")

    merged = " ".join(part for part in classes if part).strip()
    if merged:
        attrs["class"] = merged

    return field.as_widget(attrs=attrs)


@register.filter
def field_error_id(field) -> str:
    return _error_id(field)
