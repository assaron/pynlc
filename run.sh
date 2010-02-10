#!/bin/sh
CXXFLAGS=-O2 make encode
python cli.py
