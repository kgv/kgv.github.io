---
liquid:
permalink: /publications
---

# Publications

{% for publication in site.publications %}
## [{{ publication.title }}]({{ publication.url | relative_url }})

*{% for author in publication.authors %}{{ author }}{% if forloop.last != true %}, {% endif %}{% endfor %}*

DOI: link:https://doi.org/{{ publication.doi }}[{{ publication.doi }}]

{{ publication.excerpt | strip_html }}
{% endfor %}
