#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains colors used by Artella widgets
"""

from __future__ import print_function, division, absolute_import

from artella.core import qtutils

if qtutils.QT_AVAILABLE:
    from artella.externals.Qt import QtCore, QtGui

_NUMERALS = '0123456789abcdefABCDEF'
_HEXDEC = {v: int(v, 16) for v in (x + y for x in _NUMERALS for y in _NUMERALS)}


class ArtellaColors(object):

    ARTELLA = '#16a496'
    DEFAULT = ARTELLA
    RED = '#f5222d'
    GREEN = ARTELLA
    BLUE = '#1890ff'
    YELLOW = '#faad14'


def string_is_hex(color_str):
    """
    Returns whether or not given string is a valid hexadecimal color
    :param color_str: str
    :return: bool
    """

    if color_str.startswith('#'):
        color_str = color_str[1:]
    hex_regex1 = QtCore.QRegExp('^[0-9A-F]{3}$', QtCore.Qt.CaseInsensitive)
    hex_regex2 = QtCore.QRegExp('^[0-9A-F]{6}$', QtCore.Qt.CaseInsensitive)
    hex_regex3 = QtCore.QRegExp('^[0-9A-F]{8}$', QtCore.Qt.CaseInsensitive)
    if hex_regex1.exactMatch(color_str) or hex_regex2.exactMatch(color_str) or hex_regex3.exactMatch(color_str):
        return True

    return False


def rgb_from_hex(triplet):
    """
    Returns a RGB triplet from an hexadecimal value
    :param triplet: r,g,b Hexadecimal Color tuple
    """

    if triplet.startswith('#'):
        triplet = triplet[1:]

    if len(triplet) == 3:
        r, g, b = triplet[0] * 2, triplet[1] * 2, triplet[2] * 2
        return tuple([float(int(v, 16)) for v in (r, g, b)])

    return _HEXDEC[triplet[0:2]], _HEXDEC[triplet[2:4]], _HEXDEC[triplet[4:6]]


def from_string(text_color):
    """
    Returns a (int, int, int, int) format color from a string format color
    :param text_color: str, string format color to parse
    :param alpha: int, alpha of the color
    :return: (int, int, int, int)
    """

    a = 255
    if string_is_hex(text_color):
        r, g, b = rgb_from_hex(text_color)
    else:
        try:
            if text_color.startswith('rgba'):
                r, g, b, a = text_color.replace('rgba(', '').replace(')', '').split(',')
            else:
                r, g, b, a = text_color.replace('rgb(', '').replace(')', '').split(',')
        except ValueError:
            if text_color.startswith('rgba'):
                r, g, b = text_color.replace('rgba(', '').replace(')', '').split(',')
            else:
                r, g, b = text_color.replace('rgb(', '').replace(')', '').split(',')

    return QtGui.QColor(int(r), int(g), int(b), int(a))


def generate_color(primary_color, index):
    """
    Generates a new color from the given one and with given index (between 1 and 10)
    https://github.com/phenom-films/dayu_widgets/blob/master/dayu_widgets/utils.py
    :param primary_color: base color (RRGGBB)
    :param index: color step from 1 (light) to 10 (dark)
    :return: out color Color
    """

    hue_step = 2
    saturation_step = 16
    saturation_step2 = 5
    brightness_step1 = 5
    brightness_step2 = 15
    light_color_count = 5
    dark_color_count = 4

    def _get_hue(color, i, is_light):
        h_comp = color.hue()
        if 60 <= h_comp <= 240:
            hue = h_comp - hue_step * i if is_light else h_comp + hue_step * i
        else:
            hue = h_comp + hue_step * i if is_light else h_comp - hue_step * i
        if hue < 0:
            hue += 359
        elif hue >= 359:
            hue -= 359
        return hue / 359.0

    def _get_saturation(color, i, is_light):
        s_comp = color.saturationF() * 100
        if is_light:
            saturation = s_comp - saturation_step * i
        elif i == dark_color_count:
            saturation = s_comp + saturation_step
        else:
            saturation = s_comp + saturation_step2 * i
        saturation = min(100.0, saturation)
        if is_light and i == light_color_count and saturation > 10:
            saturation = 10
        saturation = max(6.0, saturation)
        return round(saturation * 10) / 1000.0

    def _get_value(color, i, is_light):
        v_comp = color.valueF()
        if is_light:
            return min((v_comp * 100 + brightness_step1 * i) / 100, 1.0)
        return max((v_comp * 100 - brightness_step2 * i) / 100, 0.0)

    light = index <= 6
    hsv_color = QtGui.QColor(primary_color) if isinstance(primary_color, str) else primary_color
    index = light_color_count + 1 - index if light else index - light_color_count - 1
    return QtGui.QColor.fromHsvF(
        _get_hue(hsv_color, index, light),
        _get_saturation(hsv_color, index, light),
        _get_value(hsv_color, index, light)
    ).name()


def fade_color(color, alpha):
    """
    Internal function that fades given color
    :param color: QColor
    :param alpha: float
    :return:
    """

    qt_color = QtGui.QColor(color)
    return 'rgba({}, {}, {}, {})'.format(qt_color.red(), qt_color.green(), qt_color.blue(), alpha)
