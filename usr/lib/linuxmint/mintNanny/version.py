#!/usr/bin/python

import apt
import sys

try:
	cache = apt.Cache()	
	pkg = cache["mintnanny"]
	print pkg.installedVersion
except:
	pass


