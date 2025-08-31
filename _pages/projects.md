---
liquid:
permalink: /projects
---

# Projects

{% for project in site.projects %}
## [{{ project.title }}]({{ project.url | relative_url }})

{{ project.excerpt | strip_html }}
{% endfor %}
