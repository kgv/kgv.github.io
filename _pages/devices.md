---
liquid:
permalink: /devices
---

# Devices

{% for device in site.devices %}
## [{{ device.title }}]({{ device.url | relative_url }})
{% endfor %}
