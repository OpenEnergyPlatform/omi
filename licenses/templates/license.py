from metadata_tool.structure import License

{% for license, display_name in licenses %}
{{display_name}} = License(
    path = "{{license.path}}",
    name = "{{license.name}}",
    identifier = "{{license.identifier}}",
    other_references = "{{license.name}}",
    text = "{{license.text}}",
    {% if license.comment %}comment = "{{license.comment}}"{% endif %})

{% endfor %}

LICENSES = { {% for license, display_name in licenses %}
    "{{license.identifier}}":{{display_name}}{%if not loop.last %},{% endif %}{% endfor %}
}
