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

from gi.repository import Gtk, GLib, GObject
from worktime import WorkTime

class WorkBalancerApp(Gtk.Window):
    def __init__(self):
        self._work_time = WorkTime()
        self._break_time = WorkTime()
        self._work_timeout_id = None
        self._break_timeout_id = None

        builder = Gtk.Builder()
        builder.add_from_file("work-balancer-gui.glade")
        # builder.connect_signals({ "on_window_destroy" : gtk.main_quit })
        ## main window
        self.window = builder.get_object("MainWindow")
        self.window.connect("delete-event", Gtk.main_quit)
        self.window.show()

        self.statusicon = Gtk.StatusIcon()
        self.statusicon.set_visible(True)
        self.statusicon.set_from_file("work-balancer-128.png")
        self.statusicon.connect("activate", self.on_status_icon_activate)

        self.min_spinner = builder.get_object("MinutesSpinner")
        self.sec_spinner = builder.get_object("SecondsSpinner")

        self._recompute_work_time()
        self.progress = builder.get_object("TimerProgress")
        self.progress.set_text(self._work_time.get_timestring())
        self.start_button = builder.get_object("StartTimerButton")
        self.start_button_image = builder.get_object("StartTimerButtonImage")

        self.stop_button = builder.get_object("StopTimerButton")

        self.break_message_textbox = builder.get_object("BreakMessageTextBox")

        self.statusbar = builder.get_object("StatusBar")

        ## options
        self.preferences_window  = builder.get_object("PreferencesWindow")
        self.preferences_window.connect("delete-event", self.on_preferences_window_delete)
        self.send_to_tray_button = builder.get_object("SendToTrayButton")
        self.timer_setting_combo = builder.get_object("TimerSettingComboBox")

        ## break window
        self.break_window = builder.get_object("BreakWindow")
        self.break_progress = builder.get_object("BreakProgress")
        self.break_label = builder.get_object("BreakLabel")

        self.break_min_spinner = builder.get_object("BreakMinutesSpinner")
        self.break_sec_spinner = builder.get_object("BreakSecondsSpinner")

        builder.connect_signals({"on_start_timer_button" : self.on_start_timer,
                                 "on_stop_timer_button" : self.on_stop_timer,
                                 "on_seconds_spinner_value_changed" : self.on_spinner_change,
                                 "on_minutes_spinner_value_changed" : self.on_spinner_change,
                                 "on_break_seconds_spinner_value_changed" : self.on_break_spinner_change,
                                 "on_break_minutes_spinner_value_changed" : self.on_break_spinner_change,
                                 "on_break_repeat_button_clicked" : self.on_break_repeat_button_click,
                                 "on_break_cancel_button_clicked" : self.on_break_cancel_button_click,
                                 "on_send_to_tray_button_clicked" : self.on_send_to_tray_button_click,
                                 "on_break_message_textbox_changed" : self.on_break_message_textbox_change,
                                 "on_preferences_button_clicked" : self.on_preferences_button_click,
                                 # options
                                 "on_enable_tray_checkbox_toggled" : self.on_enable_tray_toggle,
                                 "on_timer_setting_changed" : self.on_timer_setting_changed,
                             })

    def _recompute_break_time(self):
        m = self.break_min_spinner.get_value_as_int()
        s = self.break_sec_spinner.get_value_as_int()
        self._break_time.set_time(m, s)

    def on_spinner_change(self, spinner):
        self._recompute_work_time()
        self.progress.set_text(self._work_time.get_timestring())

    def on_break_spinner_change(self, spinner):
        self._recompute_break_time()

    def on_break_message_textbox_change(self, textbox):
        self.break_label.set_label(textbox.get_text())

    def on_send_to_tray_button_click(self, button):
        self.window.set_visible(False)

    def on_status_icon_activate(self, status_icon):
        self.window.set_visible(not self.window.get_visible())

    def on_preferences_window_delete(self, window, event):
        window.set_visible(False)
        return True

    def on_preferences_button_click(self, button):
        self.preferences_window.present()


    ### timers
    def _remove_timeout_source(self, source_id):
        if source_id:
            GLib.source_remove(source_id)

    def _recompute_work_time(self):
        m = self.min_spinner.get_value_as_int()
        s = self.sec_spinner.get_value_as_int()
        self._work_time.set_time(m, s)

    def _reset_work_timer(self):
        self._remove_timeout_source(self._work_timeout_id)
        self._recompute_work_time()
        self.progress.set_fraction(0.0)
        self.progress.set_text(self._work_time.get_timestring())

    def _start_work_timer(self, restart=False):
        if restart:
            self._stop_work_timer()
        self._recompute_work_time()
        self._work_timeout_id = GObject.timeout_add(1000, self.on_timeout, None)

    def _stop_work_timer(self):
        self._remove_timeout_source(self._work_timeout_id)
        self.progress.set_fraction(0.0)

    def on_start_timer(self, button):
        def emit_status_error(message, timeout, context_desc):
            ctx_id = self.statusbar.get_context_id(context_desc + " error")
            self.statusbar.push(ctx_id, message)
            GObject.timeout_add(timeout, lambda unused: self.statusbar.pop(ctx_id), None)

        self._recompute_break_time()

        if self._work_time.get_time(WorkTime.CURRENT) == 0:
            emit_status_error("Work time cannot be 0!", 3000, "worktime")
            return
        elif self._break_time.get_time(WorkTime.CURRENT) == 0:
            emit_status_error("Break time cannot be 0!", 3000, "breaktime")
            return

        self._work_timeout_id = GObject.timeout_add(1000, self.on_timeout, None)
        button.set_sensitive(False)
        self.stop_button.set_sensitive(True)

    def on_stop_timer(self, button):
        self._reset_work_timer()
        button.set_sensitive(False)
        self.start_button.set_sensitive(True)

    def on_timeout(self, user_data):
        value = self.progress.get_fraction() + self._work_time.get_timestep()
        do_next = self._work_time.tick()
        self.progress.set_fraction(value)
        self.progress.set_text(self._work_time.get_timestring())
        if not do_next:
            self.is_break_time = True
            self.break_window.set_visible(True)
            self.break_progress.set_fraction(0.0)
            self._recompute_break_time()
            self.break_progress.set_text(self._break_time.get_timestring())
            self._break_timeout_id = GObject.timeout_add(1000, self.on_break_timeout, None)
            return False
        return True

    ### break related stuff
    def on_break_repeat_button_click(self, button):
        self.progress.set_text(self._work_time.get_timestring())
        self._start_work_timer(True)

        self._remove_timeout_source(self._break_timeout_id)
        self.break_label.set_label("Time for a break!")
        self.break_window.set_visible(False)

    def on_break_cancel_button_click(self, button):
        self._reset_work_timer()
        self._remove_timeout_source(self._break_timeout_id)
        self.break_label.set_label("Time for a break!")
        self.break_window.set_visible(False)
        self.start_button.set_sensitive(True)
        self.stop_button.set_sensitive(False)

    def on_break_timeout(self, user_data):
        value = self.break_progress.get_fraction() + self._break_time.get_timestep()
        do_next = self._break_time.tick()
        self.break_progress.set_fraction(value)
        self.break_progress.set_text(self._break_time.get_timestring())
        if not do_next:
            self.break_label.set_label("Back to work!")
            return False
        return True

    ### options
    def on_timer_setting_changed(self, box):
        self._work_time._current_timestring_format = int(box.get_active_id())
        self.progress.set_text(self._work_time.get_timestring())

    def on_enable_tray_toggle(self, button):
        active = button.get_active()
        self.statusicon.set_visible(active)
        self.send_to_tray_button.set_sensitive(active)

if __name__ == "__main__":
    app = WorkBalancerApp()
    Gtk.main()
