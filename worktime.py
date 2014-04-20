#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright (C) 2014 Jan Synáček
#
# Author: Jan Synáček <jan.synacek@gmail.com>
# URL: https://github.com/jsynacek/work-balancer
# Created: Apr 2014
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License as
# published by the Free Software Foundation; either version 3, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street, Fifth
# Floor, Boston, MA 02110-1301, USA.

class WorkTime():
    CURRENT = 0
    TOTAL = 1

    def __init__(self):
        self._time_current = 0
        self._time_total = 0
        self._timestep = 0.0

        self._timestring_formats = {0 : "-%d:%.2d",
                                    1 : "%d:%.2d",
                                    2 : "%d:%.2d / %d:%.2d"}
        self._current_timestring_format = 0
        self._timestring = ""

    def _update_timestring(self):
        tc = self.get_time(WorkTime.CURRENT)
        tt = self.get_time(WorkTime.TOTAL)
        td = tt - tc
        f = self._timestring_formats[self._current_timestring_format]

        if self._current_timestring_format == 0:
            self._timestring = f % (tc / 60, tc % 60)
            if self._time_current == 0: # strip '-'
                self._timestring = "0:00"
        elif self._current_timestring_format == 1:
            self._timestring = f % (td / 60, td % 60)
        elif self._current_timestring_format == 2:
            self._timestring = f % (td / 60, td % 60, tt / 60, tt % 60)
        else:
            # not possible
            raise RuntimeError("Unknown timestring format: %d" % self._current_timestring_format)

    def set_time(self, m, s):
        self._time_current = m*60 + s
        self._time_total = self._time_current
        if self._time_current != 0:
            self._timestep = 1.0 / self._time_current
        self._update_timestring()

    def get_time(self, mode, in_tuple=False):
        if mode == WorkTime.CURRENT:
            time = self._time_current
        elif mode == WorkTime.TOTAL:
            time = self._time_total
        else:
            # not possible
            raise RuntimeError("Unknown mode: %d" % mode);

        if in_tuple:
            return (time / 60, time % 60)
        return time

    def get_timestep(self):
        return self._timestep

    def get_timestring(self):
        return self._timestring

    def tick(self):
        self._time_current = self._time_current - 1
        self._update_timestring()
        if self._time_current <= 0:
            self._time_current = 0
            return False
        return True
