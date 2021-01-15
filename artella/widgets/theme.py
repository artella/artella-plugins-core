#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains object to manage Artella widgets theme
"""

from __future__ import print_function, division, absolute_import

from artella.widgets import color
from artella.core import resource

_ARTELLA_THEME = None


class ArtellaTheme(object):
    def __init__(self, main_color=None):
        super(ArtellaTheme, self).__init__()

        self._init_sizes()
        self._init_fonts()
        self._init_colors()
        self.set_main_color(main_color or color.ArtellaColors.DEFAULT)

        self._default_style = resource.style('artella')
        self.unit = 'px'
        self.default_size = self.medium
        self.text_error_color = self.error_7
        self.text_color_inverse = "#fff"
        self.text_warning_color = self.warning_7

    def set_main_color(self, main_color):
        self.main_color = main_color
        self.main_color_1 = color.generate_color(main_color, 1)
        self.main_color_2 = color.generate_color(main_color, 2)
        self.main_color_3 = color.generate_color(main_color, 3)
        self.main_color_4 = color.generate_color(main_color, 4)
        self.main_color_5 = color.generate_color(main_color, 5)
        self.main_color_6 = color.generate_color(main_color, 6)
        self.main_color_7 = color.generate_color(main_color, 7)
        self.main_color_8 = color.generate_color(main_color, 8)
        self.main_color_9 = color.generate_color(main_color, 9)
        self.main_color_10 = color.generate_color(main_color, 10)
        self.item_hover_bg = self.main_color_1

    def apply(self, widget):
        widget.setStyleSheet(self._default_style.substitute(vars(self)))

    def _init_sizes(self):
        self.tiny = 18
        self.small = 24
        self.medium = 32
        self.large = 40
        self.huge = 48
        self.huge_icon = self.huge - 20
        self.large_icon = self.large - 16
        self.medium_icon = self.medium - 12
        self.small_icon = self.small - 10
        self.tiny_icon = self.tiny - 8

    def _init_fonts(self):
        self.font_family = '"Helvetica Neue",Helvetica,Arial,sans-serif'
        self.font_size_base = 14
        self.font_size_large = self.font_size_base + 2
        self.font_size_small = self.font_size_base - 2
        self.h1_size = int(self.font_size_base * 2.71)
        self.h2_size = int(self.font_size_base * 2.12)
        self.h3_size = int(self.font_size_base * 1.71)
        self.h4_size = int(self.font_size_base * 1.41)

    def _init_colors(self):
        self.artella_color = color.ArtellaColors.ARTELLA
        self.info_color = color.ArtellaColors.BLUE
        self.success_color = color.ArtellaColors.GREEN
        self.error_color = color.ArtellaColors.RED
        self.warning_color = color.ArtellaColors.YELLOW

        self.info_1 = color.fade_color(self.info_color, '15%')
        self.info_2 = color.generate_color(self.info_color, 2)
        self.info_3 = color.fade_color(self.info_color, '35%')
        self.info_4 = color.generate_color(self.info_color, 4)
        self.info_5 = color.generate_color(self.info_color, 5)
        self.info_6 = color.generate_color(self.info_color, 6)
        self.info_7 = color.generate_color(self.info_color, 7)
        self.info_8 = color.generate_color(self.info_color, 8)
        self.info_9 = color.generate_color(self.info_color, 9)
        self.info_10 = color.generate_color(self.info_color, 10)

        self.success_1 = color.fade_color(self.success_color, '15%')
        self.success_2 = color.generate_color(self.success_color, 2)
        self.success_3 = color.fade_color(self.success_color, '35%')
        self.success_4 = color.generate_color(self.success_color, 4)
        self.success_5 = color.generate_color(self.success_color, 5)
        self.success_6 = color.generate_color(self.success_color, 6)
        self.success_7 = color.generate_color(self.success_color, 7)
        self.success_8 = color.generate_color(self.success_color, 8)
        self.success_9 = color.generate_color(self.success_color, 9)
        self.success_10 = color.generate_color(self.success_color, 10)

        self.warning_1 = color.fade_color(self.warning_color, '15%')
        self.warning_2 = color.generate_color(self.warning_color, 2)
        self.warning_3 = color.fade_color(self.warning_color, '35%')
        self.warning_4 = color.generate_color(self.warning_color, 4)
        self.warning_5 = color.generate_color(self.warning_color, 5)
        self.warning_6 = color.generate_color(self.warning_color, 6)
        self.warning_7 = color.generate_color(self.warning_color, 7)
        self.warning_8 = color.generate_color(self.warning_color, 8)
        self.warning_9 = color.generate_color(self.warning_color, 9)
        self.warning_10 = color.generate_color(self.warning_color, 10)

        self.error_1 = color.fade_color(self.error_color, '15%')
        self.error_2 = color.generate_color(self.error_color, 2)
        self.error_3 = color.fade_color(self.error_color, '35%')
        self.error_4 = color.generate_color(self.error_color, 4)
        self.error_5 = color.generate_color(self.error_color, 5)
        self.error_6 = color.generate_color(self.error_color, 6)
        self.error_7 = color.generate_color(self.error_color, 7)
        self.error_8 = color.generate_color(self.error_color, 8)
        self.error_9 = color.generate_color(self.error_color, 9)
        self.error_10 = color.generate_color(self.error_color, 10)

        self.title_color = "#ffffff"
        self.main_text_color = "#d9d9d9"
        self.secondary_text_color = "#a6a6a6"
        self.disable_color = "#737373"
        self.border_color = "#1e1e1e"
        self.divider_color = "#262626"
        self.header_color = "#0a0a0a"
        self.icon_color = "#a6a6a6"
        self.background_color = "#323232"
        self.background_selected_color = "#292929"
        self.background_in_color = "#3a3a3a"
        self.background_out_color = "#494949"
        self.mask_color = color.fade_color(self.background_color, '90%')
        self.toast_color = "#555555"


def theme():
    """
    Returns Artella theme
    :return: ArtellaTheme
    """

    global _ARTELLA_THEME
    if _ARTELLA_THEME:
        return _ARTELLA_THEME

    _ARTELLA_THEME = ArtellaTheme(main_color=color.ArtellaColors.DEFAULT)

    return _ARTELLA_THEME
