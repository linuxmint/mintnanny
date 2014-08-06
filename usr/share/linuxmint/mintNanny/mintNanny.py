#!/usr/bin/env python

# MintNanny
#	Clement Lefebvre <clem@linuxmint.com>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; Version 2
# of the License.

try:
	import os
	import commands
	import sys
	import gtk
    	import gtk.glade
	import gettext
except Exception, detail:
	print detail
	pass

try:
	import pygtk
	pygtk.require("2.0")
except Exception, detail:
	print detail	
	pass

# i18n
gettext.install("mintnanny", "/usr/share/linuxmint/locale")

def open_about(widget):
	dlg = gtk.AboutDialog()
	dlg.set_title(_("About") + " - mintNanny")
	version = commands.getoutput("/usr/share/linuxmint/common/version.py mintnanny")
	dlg.set_version(version)
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
            print detail        
        dlg.set_authors(["Clement Lefebvre <root@linuxmint.com>"]) 
	dlg.set_icon_from_file("/usr/share/linuxmint/mintNanny/icon.svg")
	dlg.set_logo(gtk.gdk.pixbuf_new_from_file("/usr/share/linuxmint/mintNanny/icon.svg"))
        def close(w, res):
            if res == gtk.RESPONSE_CANCEL:
                w.hide()
        dlg.connect("response", close)
        dlg.show()

def add_domain(widget, treeview_domains):	
	name = commands.getoutput("/usr/share/linuxmint/common/entrydialog.py '" + _("Please type the domain name you want to block") + "' '" + _("Domain name:") + "' '' 'mintNanny' 2> /dev/null")
	domain = name.strip()
	if domain != '':
		model = treeview_domains.get_model()
		iter = model.insert_before(None, None)
		model.set_value(iter, 0, domain)
		domain = "127.0.0.1	" + domain + "	# blocked by mintNanny"
		os.system("echo \"" + domain + "\" >> /etc/hosts")			

def remove_domain(widget, treeview_domains):
	selection = treeview_domains.get_selection()
	(model, iter) = selection.get_selected()
	if (iter != None):
		domain = model.get_value(iter, 0)
		os.system("sed '/" + domain + "/ d' /etc/hosts > /tmp/hosts.mintNanny")
		os.system("mv /tmp/hosts.mintNanny /etc/hosts")
		model.remove(iter)

#If no backup of /etc/hosts was made, make one
if not os.path.exists("/etc/hosts.mintNanny.backup"):
	os.system("cp /etc/hosts /etc/hosts.mintNanny.backup")

#Set the Glade file
gladefile = "/usr/share/linuxmint/mintNanny/mintNanny.glade"
wTree = gtk.glade.XML(gladefile, "window1")
wTree.get_widget("window1").set_title(_("Domain Blocker"))
vbox = wTree.get_widget("vbox_main")
treeview_domains = wTree.get_widget("treeview_domains")
wTree.get_widget("window1").set_icon_from_file("/usr/share/linuxmint/mintNanny/icon.svg")

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

