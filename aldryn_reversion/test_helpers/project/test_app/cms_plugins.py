# -*- coding: utf-8 -*-
from django.template import Template

from cms.plugin_base import CMSPluginBase
from cms.plugin_pool import plugin_pool


class SamplePlugin(CMSPluginBase):
    render_template = Template('')


plugin_pool.register_plugin(SamplePlugin)
