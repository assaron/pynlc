#!/bin/sh
CXXFLAGS=-O2 make encode

case "$1" in
	-g) 
		python cli-gtk.py ;;
	
	*) 
		python cli.py
esac
