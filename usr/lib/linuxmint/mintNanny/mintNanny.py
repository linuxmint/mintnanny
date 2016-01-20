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
import gtk
import gtk.glade
import gettext
import re
import pygtk
import subprocess

# i18n
gettext.install("mintnanny", "/usr/share/linuxmint/locale")

def open_about(widget):
    dlg = gtk.AboutDialog()
    dlg.set_title(_("About") + " - mintNanny")
    output, error = subprocess.Popen(['/usr/lib/linuxmint/common/version.py', 'mintnanny'], stdout=subprocess.PIPE).communicate()
    dlg.set_version(output)
    dlg.set_program_name("mintNanny")
    dlg.set_comments(_("Domain blocker"))
    try:
        h = open('/usr/share/common-licenses/GPL','r')
        s = h.readlines()
        gpl = ""
        for line in s:
            gpl += line
        h.close()
        dlg.set_license(gpl)
    except Exception, detail:
        print (detail)
    dlg.set_authors(["Clement Lefebvre <root@linuxmint.com>"])
    dlg.set_icon_from_file("/usr/lib/linuxmint/mintNanny/icon.svg")
    dlg.set_logo(gtk.gdk.pixbuf_new_from_file("/usr/lib/linuxmint/mintNanny/icon.svg"))
    def close(w, res):
        if res == gtk.RESPONSE_CANCEL:
            w.hide()
    dlg.connect("response", close)
    dlg.show()

def add_domain(widget, treeview_domains):
    output, error = subprocess.Popen(['/usr/lib/linuxmint/common/entrydialog.py', _("Please type the domain name you want to block"), _("Domain name:"), '', 'mintNanny'], stdout=subprocess.PIPE).communicate()
    domain = re.sub(r'\s', '', output)

    if domain == '':
        # Take no action on empty input
        return

    if not is_valid_domain(domain):
        # User has passed an invalid domain (one that contains invalid characters)
        # Display an error dialog to inform them why we're not adding it to the list
        dlg = gtk.MessageDialog(parent=None, flags=gtk.DIALOG_MODAL, type=gtk.MESSAGE_ERROR, buttons=gtk.BUTTONS_OK, message_format=_("Invalid Domain"))
        desc1 = _("'%s' is not a valid domain name." % domain)
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
gladefile = "/usr/lib/linuxmint/mintNanny/mintNanny.glade"
wTree = gtk.glade.XML(gladefile, "window1")
wTree.get_widget("window1").set_title(_("Domain Blocker"))
vbox = wTree.get_widget("vbox_main")
treeview_domains = wTree.get_widget("treeview_domains")
wTree.get_widget("window1").set_icon_from_file("/usr/lib/linuxmint/mintNanny/icon.svg")

# the treeview
column1 = gtk.TreeViewColumn(_("Blocked domains"), gtk.CellRendererText(), text=0)
column1.set_sort_column_id(0)
column1.set_resizable(True)
treeview_domains.append_column(column1)
treeview_domains.set_headers_clickable(True)
treeview_domains.set_reorderable(False)
treeview_domains.show()

model = gtk.TreeStore(str)
model.set_sort_column_id( 0, gtk.SORT_ASCENDING )
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

wTree.get_widget("window1").connect("delete_event", gtk.main_quit)
wTree.get_widget("button_close").connect("clicked", gtk.main_quit)
wTree.get_widget("toolbutton_add").connect("clicked", add_domain, treeview_domains)
wTree.get_widget("toolbutton_remove").connect("clicked", remove_domain, treeview_domains)

fileMenu = gtk.MenuItem(_("_File"))
fileSubmenu = gtk.Menu()
fileMenu.set_submenu(fileSubmenu)
closeMenuItem = gtk.ImageMenuItem(gtk.STOCK_CLOSE)
closeMenuItem.get_child().set_text(_("Close"))
closeMenuItem.connect("activate", gtk.main_quit)
fileSubmenu.append(closeMenuItem)

helpMenu = gtk.MenuItem(_("_Help"))
helpSubmenu = gtk.Menu()
helpMenu.set_submenu(helpSubmenu)
aboutMenuItem = gtk.ImageMenuItem(gtk.STOCK_ABOUT)
aboutMenuItem.get_child().set_text(_("About"))
aboutMenuItem.connect("activate", open_about)
helpSubmenu.append(aboutMenuItem)

wTree.get_widget("menubar1").append(fileMenu)
wTree.get_widget("menubar1").append(helpMenu)

wTree.get_widget("window1").show_all()

gtk.main()

