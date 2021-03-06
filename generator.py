#!/usr/bin/env python3
import argparse
import collections
import datetime
import json
import os
import sys

generator_tag = '<META CONTENT="twentyonepilots.live site generator" NAME="generator" />'
macro_format = "!%s!"

def apply_macros(m, t):
	for key in m.keys():
		t = t.replace(macro_transform(key, macro_format), m[key])
	return t

def combine_macros(*args):
	retval = collections.OrderedDict()
	for arg in args:
		retval = collections.OrderedDict({**retval, **arg})
	return retval

def dates(data):
	retval = []
	for year in list(data["concerts"]):
		for month in list(data["concerts"][year]):
			for day in list(data["concerts"][year][month]):
				retval.append([year, month, day])
	return retval

# print an error to stderr and then exit 1
def error(s):
	sys.stderr.write("%s: %s\n" % (sys.argv[0], s))
	sys.exit(1)

# safely read a file
# n
#	file name
def fileread(n):
	try:
		f = open(n)
	except FileNotFoundError as e:
		error(e)
	r = f.read()
	f.close()
	return r

# safely write a file
# n
#	file name
# c
#	content
def filewrite(n, c):
	try:
		f = open(n, "w")
	except Exception as e:
		error(e)
	f.write(c)
	f.close()
	return

# mkdir -p {$years}/{$months}, you get the idea
def generate_directory_structure(data):
	for year in list(data["concerts"]):
		if not(os.path.exists(year)):
			try:
				os.mkdir(year)
			except Exception as e:
				error("Error generating directory structure (os.mkdir): %s" % e)
		os.chdir(year)
		for month in list(data["concerts"][year]):
			if not(os.path.exists(month)):
				try:
					os.mkdir(month)
				except Exception as e:
					error("Error generating directory structure (os.mkdir): %s" % e)
		os.chdir("..")
	return

def generate_index(data, template):
	content = ""

	content += "<UL>\n"
	for date in dates(data):
		content += '<LI><A HREF="/%s/%s/%s.html">%s-%s-%s: %s</A></LI>\n' \
			% (date[0], date[1], date[2], date[0], date[1], date[2],
				data["concerts"][date[0]][date[1]][date[2]]["venue"])
	content += "</UL>\n"

	filewrite(
		"index.html", apply_macros(
			combine_macros(
				macros(data), collections.OrderedDict([("Content", content)])
			), template
		)
	)


def generate_pages(data, template):
	for date in dates(data):
		filewrite(
			"%s/%s/%s.html" % tuple(date),
			apply_macros(
				combine_macros(
					macros(data),
					macros_page(data, date)
				), template
			)
		)
	return

def macros(data):
	macros = collections.OrderedDict([("Generator", generator_tag)])
	return macros

# data
#	the full JSON object
# selection
#	A list of [
#		the year of the performance selected (str, len 4)
#		the month of the performance selected (str, len 2)
#		the day of the performance selected (str, len 2)
#	]
def macros_page(data, selection):
	year = selection[0]
	month = selection[1]
	day = selection[2]
	try:
		concert = data["concerts"][year][month][day]
	except KeyError as e:
		error("macros_page(): KeyError: %s" % e)

	# trivial date macros to start out
	macros = collections.OrderedDict([
		("DY", year),
		("DM", month),
		("DD", day),
		("Dp", datetime.date(int(year), int(month), int(day)).strftime("%d %B %Y"))
	])


	macros["Venue"] = concert["venue"]

	# embed
	embed= data["concerts"][year][month][day]["embed"]
	if embed["type"] == "none":
		pass
	elif embed["type"] == "iframe":
		macros["Embed"] = '''\
<IFRAME
ALLOWFULLSCREEN
FRAMEBORDER="0"
HEIGHT="480"
MOZALLOWFULLSCREEN="true"
SRC="%s"
WEBKITALLOWFULLSCREEN="true"
WIDTH="640"
><P><A HREF="%s">iframe</A></P></IFRAME>''' % (embed["href"], embed["href"])
	else:
		error("What embed type is %s? (%s)"
			% (embed["type"], ('data["concerts"]["%s"]["%s"]["%s"]["embed"]["type"]'
				% (year, month, day))))

	# setlist ordered list
	setlist = "<OL>\n"
	for s in concert["setlist"]:
		setlist += "<LI>%s</LI>\n" % s
	setlist += "</OL>\n"
	macros["Setlist"] = setlist

	return macros

# turn a macro name into the string for which to search to turn into macro
# content
# in: "hello world", "!%s!"
# out: "!hello world!"
def macro_transform(s, fmt):
	return fmt % s

def main(argc, argv):
	try:
		data = json.loads(fileread("data.json"))
	except json.decoder.JSONDecodeError as e:
		error("Invalid JSON file. (%s)" % e)

	template = {
		"index": fileread("index.html.template"),
		"pages": fileread("XX.html.template")
	}
	os.chdir("docs")

	generate_directory_structure(data)
	generate_index(data, template["index"])
	generate_pages(data, template["pages"])

	return 0;

if __name__ == "__main__":
	sys.exit(main(len(sys.argv), sys.argv))
