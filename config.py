# -*- coding: utf-8 -*-
# 
# Copyrigt 2010 Aleksey Sergushichev <alsergbox@gmail.com>
# 
# This file is part of pynlc.

# Pynlc is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Pynlc is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with pynlc.  If not, see <http://www.gnu.org/licenses/>.

from datetime import date, datetime

ADDRES = "192.168.111.210"
#ADDRES = "localhost"
PORT = 1539
SERVER = (ADDRES, PORT)
BUF_SIZE = 1024

EPOCH_START_SECONDS = datetime(2000, 1, 1)
EPOCH_START_DAYS = date(1899, 12, 30)


NC_HASH = "02d45b64"
NC_VERSION = "v8.6"

