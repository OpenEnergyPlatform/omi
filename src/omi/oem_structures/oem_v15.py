'''
This module extends the internal data structure 
with the latest changes of the OEMetadata standard.

An OEMeadata version specific dialect can import it.

This bypasses the limitation of OMI to rely on a single 
internal representation of the data structure, since 
OEMetadata is not a static structure and OMI must be
be able to validate multiple OEMetadata versions.
'''

from datetime import datetime
from enum import Enum
from typing import Iterable
from omi.structure import Compilable

