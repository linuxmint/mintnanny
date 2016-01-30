#!/usr/bin/python3

# MintNanny
#   Clement Lefebvre <clem@linuxmint.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; Version 2
# of the License.

import os
import sys
from gi.repository import Gtk, Gdk
import gettext
import re
import fileinput

# i18n
gettext.install("mintnanny", "/usr/share/linuxmint/locale")


class MintNanny():

    def __init__(self):
        # Set the Glade file
        gladefile = "/usr/share/linuxmint/mintnanny/mintnanny.ui"
        builder = Gtk.Builder()
        builder.add_from_file(gladefile)
        self.window = builder.get_object("main_window")
        self.window.set_title(_("Domain Blocker"))
        self.window.set_icon_name("mintnanny")

        # the treeview
        column = Gtk.TreeViewColumn(_("Blocked domains"), Gtk.CellRendererText(), text=0)
        column.set_sort_column_id(0)
        column.set_resizable(True)
        self.treeview = builder.get_object("treeview_domains")
        self.treeview.append_column(column)
        self.treeview.set_headers_clickable(True)
        self.treeview.set_reorderable(False)
        self.treeview.show()
        self.model = Gtk.TreeStore(str)
        self.model.set_sort_column_id(0, Gtk.SortType.ASCENDING)
        self.treeview.set_model(self.model)

        # Get the list of allowed domains
        with open("/etc/hosts") as f:
            for line in f:
                if '0.0.0.0' in line or 'blocked by mintNanny' in line:
                    elements = line.split()
                    if len(elements) > 1:
                        domain = elements[1]
                        iter = self.model.insert_before(None, None)
                        self.model.set_value(iter, 0, domain)

        self.window.connect("delete_event", Gtk.main_quit)
        builder.get_object("toolbutton_add").connect("clicked", self.add_domain)
        self.remove_button = builder.get_object("toolbutton_remove")
        self.remove_button.connect("clicked", self.remove_domain)
        self.remove_button.set_sensitive(False)
        self.treeview.get_selection().connect("changed", self.on_domain_selected)

        self.window.show_all()

    def ask_domain_name(self):
        dialogWindow = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, _("Please type the domain name you want to block"))
        dialogWindow.set_title(_("Domain name"))
        dialogBox = dialogWindow.get_content_area()
        entry = Gtk.Entry()
        entry.set_activates_default(True)
        box = Gtk.Box()
        box.pack_start(entry, True, True, 12)
        dialogBox.pack_start(box, True, True, 0)
        okButton = dialogWindow.get_widget_for_response(response_id=Gtk.ResponseType.OK)
        okButton.set_can_default(True)
        okButton.grab_default()
        dialogWindow.show_all()
        response = dialogWindow.run()
        text = entry.get_text()
        dialogWindow.destroy()
        if (response == Gtk.ResponseType.OK) and (text != ''):
            return text
        else:
            return None

    def add_domain(self, widget):
        domain = self.ask_domain_name()
        if domain is None or domain == '':
            # Take no action on empty input
            return
        domain = re.sub(r'\s', '', domain)
        if domain.startswith('www.'):
            domain = domain[4:]
        if not self.is_valid_domain(domain):
            # User has passed an invalid domain (one that contains invalid characters)
            # Display an error dialog to inform them why we're not adding it to the list
            dlg = Gtk.MessageDialog(type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, message_format=_("Invalid Domain"))
            dlg.set_transient_for(self.window)
            desc1 = _("%s is not a valid domain name." % domain)
            desc2 = _("Domain names must start and end with a letter or a digit, and can only contain letters, digits, dots and hyphens.")
            desc3 = _("Example: my.number1domain.com")
            dlg.format_secondary_text("%s\n\n%s\n\n%s" % (desc1, desc2, desc3))
            dlg.run()
            dlg.destroy()
            return

        prefixes = [""]
        if len(domain.split(".")) == 2:
            # domain in the form 'domainname.extension'
            prefixes.append("www.")
        for prefix in prefixes:
            full_domain = "%s%s" % (prefix, domain)
            iter = self.model.insert_before(None, None)
            self.model.set_value(iter, 0, full_domain)
            os.system("echo \"127.0.0.1 %s # blocked by mintNanny\" >> /etc/hosts" % full_domain)

    def on_domain_selected(self, selection):
        model, treeiter = selection.get_selected()
        self.remove_button.set_sensitive(treeiter != None)

    def remove_domain(self, widget):
        selection = self.treeview.get_selection()
        (model, iter) = selection.get_selected()
        if (iter != None):
            domain = model.get_value(iter, 0)
            for line_number, line in enumerate(fileinput.input('/etc/hosts', inplace=1)):
                found = False
                if '0.0.0.0' in line or 'blocked by mintNanny' in line:
                    elements = line.split()
                    if len(elements) > 1:
                        if elements[1] == domain:
                            found = True
                if not found:
                    sys.stdout.write(line)
            model.remove(iter)

    def is_valid_domain(self, domain):
        # Quick sanity check
        if domain == '' or "." not in domain:
            return False

        # The following is based on RFC 952 (https://tools.ietf.org/html/rfc952)
        # and section 2.1 of RFC 1123 (https://tools.ietf.org/html/rfc1123#page-13)
        # Also see sections 2.3.1 and 2.3.4 of RFC 1035 (http://tools.ietf.org/html/rfc1035)

        # Quick regex match to check the domain name's sanity
        # Note: This enforces that the domain name starts with a letter or a digit
        # This does NOT enforce the label size limits (63 characters max in-between dots)
        regex = re.compile('^[A-Za-z0-9][A-Za-z0-9\-\.]+$')
        if not regex.match(domain):
            return False

        # A domain name MUST end with an alphanumeric character
        # At this point we're certain that the string only contains alphanumeric characters or hyphens and dots.
        # So we just need to check that it doesn't end with a hyphen or a dot
        if domain.endswith('-') or domain.endswith('.'):
            return False

        # Domain names have a length limit of 255 characters
        if len(domain) > 255:
            return False

        return True

if __name__ == "__main__":
    # If no backup of /etc/hosts was made, make one
    if not os.path.exists("/etc/hosts.mintnanny.backup"):
        os.system("cp /etc/hosts /etc/hosts.mintnanny.backup")
    MintNanny()
    Gtk.main()
