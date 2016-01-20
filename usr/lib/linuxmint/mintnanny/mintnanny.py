#!/usr/bin/python2

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
import subprocess

# i18n
gettext.install("mintnanny", "/usr/share/linuxmint/locale")

def ask_domain_name(window):
    dialogWindow = Gtk.MessageDialog(window, Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT, Gtk.MessageType.QUESTION, Gtk.ButtonsType.OK_CANCEL, _("Please type the domain name you want to block"))
    dialogWindow.set_title(_("Domain name"))
    dialogBox = dialogWindow.get_content_area()
    userEntry = Gtk.Entry()
    dialogBox.pack_end(userEntry, False, False, 0)
    dialogWindow.show_all()
    response = dialogWindow.run()
    text = userEntry.get_text()
    dialogWindow.destroy()
    if (response == Gtk.ResponseType.OK) and (text != ''):
        return text
    else:
        return None

def add_domain(widget, treeview_domains, window):
    domain = ask_domain_name(window)
    if domain is None or domain == '':
        # Take no action on empty input
        return
    domain = re.sub(r'\s', '', domain)
    if not is_valid_domain(domain):
        # User has passed an invalid domain (one that contains invalid characters)
        # Display an error dialog to inform them why we're not adding it to the list
        dlg = Gtk.MessageDialog(type=Gtk.MessageType.ERROR, buttons=Gtk.ButtonsType.OK, message_format=_("Invalid Domain"))
        dlg.set_transient_for(window)
        desc1 = _("%s is not a valid domain name." % domain)
        desc2 = _("Domain names must start and end with a letter or a digit, and can only contain letters, digits, dots and hyphens.")
        desc3 = _("Example: my.number1domain.com")
        dlg.format_secondary_text("%s\n\n%s\n\n%s" % (desc1, desc2, desc3))
        dlg.run()
        dlg.destroy()
        return

    model = treeview_domains.get_model()
    iter = model.insert_before(None, None)
    model.set_value(iter, 0, domain)
    domain = "127.0.0.1 " + domain + "  # blocked by mintNanny"
    os.system("echo \"" + domain + "\" >> /etc/hosts")

def remove_domain(widget, treeview_domains):
    selection = treeview_domains.get_selection()
    (model, iter) = selection.get_selected()
    if (iter != None):
        domain = model.get_value(iter, 0)
        os.system("sed '/" + domain + "/ d' /etc/hosts > /tmp/hosts.mintNanny")
        os.system("mv /tmp/hosts.mintNanny /etc/hosts")
        model.remove(iter)

def is_valid_domain(domain):
    #Quick sanity check
    if domain == '':
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

#If no backup of /etc/hosts was made, make one
if not os.path.exists("/etc/hosts.mintNanny.backup"):
    os.system("cp /etc/hosts /etc/hosts.mintNanny.backup")

#Set the Glade file
gladefile = "/usr/share/linuxmint/mintnanny/mintnanny.ui"
builder=Gtk.Builder()
builder.add_from_file(gladefile)
window = builder.get_object("window1")
window.set_title(_("Domain Blocker"))
vbox = builder.get_object("vbox_main")
treeview_domains = builder.get_object("treeview_domains")
window.set_icon_name("mintnanny")

# the treeview
column1 = Gtk.TreeViewColumn(_("Blocked domains"), Gtk.CellRendererText(), text=0)
column1.set_sort_column_id(0)
column1.set_resizable(True)
treeview_domains.append_column(column1)
treeview_domains.set_headers_clickable(True)
treeview_domains.set_reorderable(False)
treeview_domains.show()

model = Gtk.TreeStore(str)
model.set_sort_column_id( 0, Gtk.SortType.ASCENDING )
treeview_domains.set_model(model)

#Get the list of allowed domains
hostsFile = open("/etc/hosts")
for line in hostsFile:
    line = str.strip(line)
    if line.find('0.0.0.0') > -1 or line.find('blocked by mintNanny') > -1:
        elements = line.split("\t")
        domain = elements[1]
        iter = model.insert_before(None, None)
        model.set_value(iter, 0, domain)
del model

window.connect("delete_event", Gtk.main_quit)
builder.get_object("toolbutton_add").connect("clicked", add_domain, treeview_domains, window)
builder.get_object("toolbutton_remove").connect("clicked", remove_domain, treeview_domains)

window.show_all()

Gtk.main()
